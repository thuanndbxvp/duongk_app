# MSEW: phase5-audit-fixes-foundation

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase5-audit-fixes-foundation.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase5-audit-fixes-foundation.md`
- **Migration hiện tại cuối:** `supabase/migrations/0021_voice_profiles.sql`
- **Branch:** main (chưa có branch riêng)
- **Working dir:** `d:\appDK`
- **Line ending:** CRLF (giữ nguyên khi edit file cũ)
- **Quy tắc:** KHÔNG tự sửa code ngoài scope. Nếu fail → `BLOCKERS.md`.

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Drop duplicate `hold_credits` signature cũ | `databases` | `backend-development` | `debugging` |
| 2 | Fix RLS `transcripts` (0011) | `databases` | `better-auth` | `debugging` |
| 3 | Migration 0022: thêm column role/max_assistants/banned_at/deleted_at/last_sign_in_at + bảng admin_audit_logs | `databases` | `backend-development` | `planning` |
| 4 | RPC `admin_adjust_credits` + `soft_delete_user` | `databases` | `backend-development` | `debugging` |
| 5 | Thêm helper `get_user_role()` vào `credit_manager.py` | `backend-development` | `better-auth` | `databases` |
| 6 | Tạo `apps/api/dependencies/admin.py:require_admin` | `better-auth` | `backend-development` | `debugging` |
| 7 | Tạo `apps/api/services/audit.py:log_admin_action` | `backend-development` | `better-auth` | `code-review` |
| 8 | Tạo `apps/web/middleware.ts` | `frontend-development` | `web-frameworks` | `better-auth` |
| 9 | Tạo `apps/web/app/(admin)/layout.tsx` (AdminShell) | `frontend-development` | `ui-styling` | `aesthetic` |
| 10 | Tạo `apps/web/app/(admin)/admin/page.tsx` (4 stat cards placeholder) | `frontend-development` | `ui-styling` | `aesthetic` |
| 11 | Update `.env.example` (thêm ADMIN_ALLOWED_IPS) | `backend-development` | `debugging` | — |
| 12 | Self-verify toàn bộ | `debugging` | `code-review` | `backend-development` |

## Files KHÔNG được đụng (Do Not Touch)
- `apps/api/routers/projects.py` — production route đang chạy.
- `apps/api/modules/voice/routes.py` — TTS đang hoạt động.
- `apps/api/modules/transcript/engine.py` — logic engine tốt, chỉ fix RLS ở Step 2.
- `apps/web/app/(dashboard)/**` — UI user-facing, không thuộc scope.
- `supabase/migrations/0001..0021` — không xoá/sửa, chỉ thêm 0022.

---

## Micro-Steps

### Step 1: Drop duplicate `hold_credits` signature cũ
**File:** `supabase/migrations/0022_admin_panel_foundation.sql` (NEW)
**Vị trí:** Đầu file, sau header comment.
**Skill Invocation:**
  - **Primary:** `databases` — SQL DROP FUNCTION.
  - **Reference:** `backend-development` — xác nhận signature qua codegraph.
  - **Fallback:** `debugging` — nếu DROP fail.

**Pre-check (CodeGraph):**
- `codegraph_node`: `hold` (apps/api/services/credit_manager.py:41) ➔ confirm signature `(self, user_id: str, job_id: str, amount: int)` calls `rpc('hold_credits', {p_user_id, p_amount, p_job_id})` ➔ order đã đúng với 0020.

**Import cần thêm:** (không — SQL migration)

**Code cần viết:**
```sql
-- 0022_admin_panel_foundation.sql
-- ============================================================
-- Migration: 0022_admin_panel_foundation.sql
-- Purpose: Cleanup + admin RBAC foundation
-- ============================================================

-- 1) Cleanup: xóa signature cũ của hold_credits (từ 0006) để tránh ambiguity
DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS release_credits(UUID, UUID);
```

**Post-verify (CodeGraph):**
- `codegraph_search`: `hold_credits` ➔ chỉ còn 1 definition ở 0020.
- `codegraph_impact`: `hold` method ➔ 1 caller (`start_project`) ➔ không ảnh hưởng.

**KHÔNG được sửa:**
- Không sửa các function trong 0020 (chỉ DROP function cũ).

**Verify command (PowerShell):**
```powershell
# Giả lập: nếu có Supabase local đang chạy
supabase db reset --linked
# Hoặc kiểm tra cú pháp SQL
Get-Content supabase\migrations\0022_admin_panel_foundation.sql | ForEach-Object { $_ }
```

**Expected output:** File SQL hợp lệ, không có lỗi syntax. Nếu có `supabase db reset` chạy được → 2 function cũ bị xóa.

**Nếu fail:** Invoke skill `debugging`. Báo cáo vào `BLOCKERS.md`.

---

### Step 2: Fix RLS `transcripts` (0011)
**File:** `supabase/migrations/0022_admin_panel_foundation.sql` (APPEND to Step 1)
**Vị trí:** Sau block DROP FUNCTION, trước phần thêm column.
**Skill Invocation:**
  - **Primary:** `databases` — SQL RLS.
  - **Reference:** `better-auth` — auth.uid() pattern.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- (Không có symbol Python liên quan — pure SQL)
- `codegraph_search`: `transcripts` table ➔ exists ở `0011_transcripts_cron.sql`.

**Import cần thêm:** (không)

**Code cần viết (APPEND vào file Step 1):**
```sql
-- 2) Fix RLS transcripts: scope theo assistant_id thay vì 'all authenticated'
-- Xóa policy cũ "Authenticated users can view transcripts"
DROP POLICY IF EXISTS "Authenticated users can view transcripts" ON transcripts;

-- Policy mới: cho phép user đọc transcripts thuộc các assistant của mình
-- (qua JOIN bảng dna_chunks → assistant_id)
CREATE POLICY "Users can view own assistant transcripts" ON transcripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM dna_chunks dc
      JOIN channel_assistants ca ON ca.id = dc.assistant_id
      WHERE dc.source_video_id = transcripts.video_id
        AND ca.user_id = auth.uid()
    )
  );

-- Service role vẫn đọc được (cho worker ghi transcripts)
CREATE POLICY "Service can insert transcripts" ON transcripts FOR INSERT
  WITH CHECK (true);
```

**Post-verify (CodeGraph):**
- (Không có)

**KHÔNG được sửa:**
- Không xóa `pg_cron` job `transcript-cleanup`.

**Verify command:**
```powershell
Get-Content supabase\migrations\0022_admin_panel_foundation.sql | Select-String "POLICY"
```

**Expected output:** Có 2 POLICY: 1 SELECT mới + 1 INSERT cho service.

**Nếu fail:** Check xem `dna_chunks.assistant_id` đã được khai báo đúng ở `0010_dna_chunks.sql` (đã có FK).

---

### Step 3: Migration 0022 — ALTER TABLE users + CREATE TABLE admin_audit_logs
**File:** `supabase/migrations/0022_admin_panel_foundation.sql` (APPEND)
**Vị trí:** Sau Step 2.
**Skill Invocation:**
  - **Primary:** `databases`.
  - **Reference:** `backend-development`.
  - **Fallback:** `planning`.

**Pre-check (CodeGraph):**
- `codegraph_search`: `users` table ➔ columns hiện tại: `id, email, credits, tier, created_at, updated_at` (đã verify ở 0001).

**Code cần viết (APPEND):**
```sql
-- 3) ALTER TABLE users: thêm columns cho admin RBAC + soft delete + ban
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
    CHECK (role IN ('user', 'admin', 'super_admin')),
  ADD COLUMN IF NOT EXISTS max_assistants INT NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS banned_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS banned_reason TEXT,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_sign_in_at TIMESTAMPTZ;

-- Partial index: chỉ index user chưa xoá
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier) WHERE deleted_at IS NULL;

-- 4) Bảng admin_audit_logs
CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID NOT NULL REFERENCES users(id),
  admin_email TEXT NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  before JSONB,
  after JSONB,
  ip INET,
  user_agent TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_admin ON admin_audit_logs(admin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_target ON admin_audit_logs(target_type, target_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON admin_audit_logs(action, created_at DESC);

-- RLS: deny non-service, chỉ service_role mới đọc/ghi
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
-- (không tạo policy → mặc định deny cho non-service)
```

**Post-verify (CodeGraph):**
- (SQL only)

**Verify command:**
```powershell
Get-Content supabase\migrations\0022_admin_panel_foundation.sql | Measure-Object -Line
```

**Expected output:** Line count ≥ 30.

---

### Step 4: RPC `admin_adjust_credits` + `soft_delete_user`
**File:** `supabase/migrations/0022_admin_panel_foundation.sql` (APPEND)
**Skill Invocation:**
  - **Primary:** `databases` — SQL functions.
  - **Reference:** `backend-development` — sẽ gọi từ admin router.
  - **Fallback:** `debugging`.

**Code cần viết (APPEND):**
```sql
-- 5) RPC admin_adjust_credits (atomic + audit-ready)
CREATE OR REPLACE FUNCTION admin_adjust_credits(
  p_admin_id UUID,
  p_user_id UUID,
  p_delta INT,
  p_reason TEXT
) RETURNS TABLE(new_balance INT, tx_id UUID) AS $$
DECLARE
  v_current INT;
  v_tx_id UUID;
BEGIN
  IF p_reason IS NULL OR length(trim(p_reason)) < 10 THEN
    RAISE EXCEPTION 'Reason required (min 10 chars)';
  END IF;

  SELECT credits INTO v_current FROM users WHERE id = p_user_id FOR UPDATE;
  IF v_current IS NULL THEN RAISE EXCEPTION 'User not found'; END IF;

  UPDATE users SET credits = credits + p_delta, updated_at = NOW() WHERE id = p_user_id;

  INSERT INTO credit_transactions (user_id, action, amount, balance_after, reason, metadata)
  VALUES (p_user_id, 'admin_adjust', p_delta, v_current + p_delta, p_reason,
          jsonb_build_object('admin_id', p_admin_id))
  RETURNING id INTO v_tx_id;

  RETURN QUERY SELECT v_current + p_delta, v_tx_id;
END;
$$ LANGUAGE plpgsql;

-- 6) RPC soft_delete_user
CREATE OR REPLACE FUNCTION soft_delete_user(p_user_id UUID) RETURNS void AS $$
BEGIN
  UPDATE users SET deleted_at = NOW() WHERE id = p_user_id AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;
```

**Verify command:**
```powershell
# Check SQL parse (requires psql installed, optional)
# psql -d postgres -c "SELECT 1" > $null; if ($?) { echo 'psql OK' }
Get-Content supabase\migrations\0022_admin_panel_foundation.sql | Select-String "CREATE OR REPLACE FUNCTION"
```

**Expected output:** 2 function `CREATE OR REPLACE FUNCTION`.

---

### Step 5: Thêm helper `get_user_role()` vào `credit_manager.py`
**File:** `apps/api/services/credit_manager.py`
**Vị trí:** Dòng 6, ngay sau import `get_supabase_admin` (sau import block hiện tại).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `databases`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `CreditManager.__init__` ➔ signature `(self)` ➔ dùng `get_supabase_admin()`.

**Import cần thêm:** (không — đã có `get_supabase_admin`)

**Code cần viết (sửa file):**
- Mở file `apps/api/services/credit_manager.py`
- Tìm block `class CreditManager:` (line 20)
- SAU dòng `def __init__(self):` (line 23) và TRƯỚC `def get_pricing` (line 26), thêm hàm **module-level** (không trong class):

```python
def get_user_role(user_id: str) -> str:
    """
    Lấy role của user từ bảng users.
    
    Args:
        user_id: UUID string của user.
    
    Returns:
        'user' | 'admin' | 'super_admin'. Default 'user' nếu user không tồn tại.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('users')
        .select('role')
        .eq('id', user_id)
        .single()
        .execute()
    )
    if result.data and 'role' in result.data:
        return result.data['role']
    return 'user'
```

**KHÔNG được sửa:**
- Không đụng `PRICING` dict, `class CreditManager`, các method `hold/adjust/commit/refund`.

**Verify command:**
```powershell
python -c "from apps.api.services.credit_manager import get_user_role; print('OK')"
```

**Expected output:** `OK` (không có lỗi import).

**Nếu fail:** Check import path. Có thể cần `cd apps/api` trước.

---

### Step 6: Tạo `apps/api/dependencies/admin.py`
**File:** `apps/api/dependencies/admin.py` (NEW)
**Skill Invocation:**
  - **Primary:** `better-auth`.
  - **Reference:** `backend-development`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `get_supabase_user` (apps/api/dependencies/auth.py:14) ➔ signature `-> str`.

**Import cần thêm:** (đã có sẵn các module)

**Code cần viết:**
```python
"""
RBAC dependency cho admin endpoints.
Yêu cầu user có role 'admin' hoặc 'super_admin'.
"""
import functools
from fastapi import Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.services.credit_manager import get_user_role


_ROLE_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 60  # seconds


def require_admin(user_id: str = Depends(get_supabase_user)) -> str:
    """
    Verify user có role admin/super_admin.
    
    Args:
        user_id: Từ JWT (auto-injected bởi get_supabase_user).
    
    Returns:
        user_id nếu pass.
    
    Raises:
        HTTPException 403 nếu không phải admin.
    """
    import time
    
    cached = _ROLE_CACHE.get(user_id)
    if cached:
        role, expires_at = cached
        if time.time() < expires_at:
            if role not in ('admin', 'super_admin'):
                raise HTTPException(403, 'Admin only')
            return user_id
    
    role = get_user_role(user_id)
    _ROLE_CACHE[user_id] = (role, time.time() + _CACHE_TTL)
    
    if role not in ('admin', 'super_admin'):
        raise HTTPException(403, 'Admin only')
    return user_id
```

**Verify command:**
```powershell
python -c "from apps.api.dependencies.admin import require_admin; print('OK')"
```

**Expected output:** `OK`.

---

### Step 7: Tạo `apps/api/services/audit.py`
**File:** `apps/api/services/audit.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `code-review`.

**Import cần thêm:** (không — file mới)

**Code cần viết:**
```python
"""
Audit log service cho admin actions.
Tự động mask các field nhạy cảm (key/secret/token/password).
"""
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_admin


_SENSITIVE_KEYS = re.compile(r'(key|token|secret|password|api_key)', re.IGNORECASE)


def _mask_value(obj: Any) -> Any:
    """Deep-copy object, thay thế value của sensitive keys bằng '***'."""
    if isinstance(obj, dict):
        return {
            k: ('***' if _SENSITIVE_KEYS.search(str(k)) else _mask_value(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_mask_value(item) for item in obj]
    return obj


def log_admin_action(
    admin_id: UUID,
    admin_email: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """
    Ghi một admin action vào bảng admin_audit_logs.
    
    Args:
        admin_id: UUID của admin thực hiện.
        admin_email: Email admin (denormalized để hiển thị).
        action: Tên action, vd 'user.update', 'credit.adjust'.
        target_type: Loại target, vd 'user', 'credit', 'api_key'.
        target_id: UUID hoặc composite key của target.
        before: Snapshot trước khi thay đổi (sẽ tự mask).
        after: Snapshot sau khi thay đổi (sẽ tự mask).
        ip: IP address (ưu tiên X-Forwarded-For).
        user_agent: User agent string.
        reason: Lý do (bắt buộc cho sensitive actions).
    """
    admin = get_supabase_admin()
    admin.table('admin_audit_logs').insert({
        'admin_id': str(admin_id),
        'admin_email': admin_email,
        'action': action,
        'target_type': target_type,
        'target_id': target_id,
        'before': _mask_value(before) if before else None,
        'after': _mask_value(after) if after else None,
        'ip': ip,
        'user_agent': user_agent,
        'reason': reason,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }).execute()
```

**Verify command:**
```powershell
python -c "from apps.api.services.audit import log_admin_action, _mask_value; masked = _mask_value({'openai_key': 'sk-xxx', 'name': 'foo'}); print(masked)"
```

**Expected output:** `{'openai_key': '***', 'name': 'foo'}`

---

### Step 8: Tạo `apps/web/middleware.ts`
**File:** `apps/web/middleware.ts` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `web-frameworks`.
  - **Fallback:** `better-auth`.

**Pre-check (CodeGraph):**
- (Không có Python liên quan — chỉ Next.js middleware)
- Check repo hiện có `@supabase/ssr` package: đã có (xem apps/web/package.json).

**Code cần viết:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@supabase/ssr';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Chỉ apply cho /admin/* và /api/admin/*
  if (!pathname.startsWith('/admin') && !pathname.startsWith('/api/admin')) {
    return NextResponse.next();
  }

  const response = NextResponse.next();

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: any) {
          response.cookies.set({ name, value, ...options });
        },
        remove(name: string, options: any) {
          response.cookies.set({ name, value: '', ...options });
        },
      },
    }
  );

  const { data: { session } } = await supabase.auth.getSession();

  // Chưa login → redirect to /login
  if (!session) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Check role
  const { data: userData } = await supabase
    .from('users')
    .select('role')
    .eq('id', session.user.id)
    .single();

  const role = (userData?.role as string) || 'user';

  if (!['admin', 'super_admin'].includes(role)) {
    return NextResponse.redirect(new URL('/403', request.url));
  }

  return response;
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
};
```

**Verify command:**
```powershell
# Check syntax bằng cách build nhỏ
cd apps\web
pnpm exec tsc --noEmit middleware.ts 2>&1 | Select-String "error"
```

**Expected output:** Không có dòng nào chứa "error".

---

### Step 9: Tạo `apps/web/app/(admin)/layout.tsx` (AdminShell)
**File:** `apps/web/app/(admin)/layout.tsx` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Pre-check (CodeGraph):**
- `codegraph_node`: layout pattern tồn tại ở `apps/web/app/(dashboard)/layout.tsx` ➔ dùng `TopBar` + `AuthenticatedLayout`.

**Code cần viết:**
```typescript
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { IconDashboard, IconUsers, IconChannels, IconShield, IconAlert } from '@/components/icons';

const ADMIN_NAV = [
  { href: '/admin', label: 'Dashboard', icon: IconDashboard, enabled: true },
  { href: '/admin/users', label: 'Users', icon: IconUsers, enabled: false },
  { href: '/admin/credits', label: 'Credits', icon: IconChannels, enabled: false },
  { href: '/admin/pricing', label: 'Pricing', icon: IconShield, enabled: false },
  { href: '/admin/api-keys', label: 'API Keys', icon: IconShield, enabled: false },
  { href: '/admin/routing', label: 'Routing', icon: IconChannels, enabled: false },
  { href: '/admin/alerts', label: 'Alerts', icon: IconAlert, enabled: false },
  { href: '/admin/audit-logs', label: 'Audit Logs', icon: IconShield, enabled: false },
];

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
      },
    }
  );

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) redirect('/login?next=/admin');

  const { data: userData } = await supabase
    .from('users')
    .select('role, email')
    .eq('id', session.user.id)
    .single();

  const role = (userData?.role as string) || 'user';
  if (!['admin', 'super_admin'].includes(role)) redirect('/403');

  return (
    <div className="min-h-screen flex bg-[var(--bg)]">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-[var(--glass-border)] bg-[var(--surface)] flex flex-col">
        <div className="px-5 py-5 border-b border-[var(--glass-border)]">
          <Link href="/admin" className="text-lg font-bold gradient-text">
            Admin Panel
          </Link>
          <p className="text-xs text-[var(--fg-tertiary)] mt-1">
            {userData?.email}
          </p>
          <span className="inline-block mt-2 px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
            {role}
          </span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {ADMIN_NAV.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.enabled ? item.href : '#'}
                aria-disabled={!item.enabled}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  item.enabled
                    ? 'text-[var(--fg-secondary)] hover:bg-[var(--surface-hover)] hover:text-white'
                    : 'text-[var(--fg-tertiary)] cursor-not-allowed opacity-50'
                }`}
              >
                <Icon size={16} />
                <span>{item.label}</span>
                {!item.enabled && (
                  <span className="ml-auto text-[10px] uppercase tracking-wider opacity-60">
                    Soon
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
        <div className="px-5 py-4 border-t border-[var(--glass-border)] text-xs text-[var(--fg-tertiary)]">
          v0.1.0 · Phase 5
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

**Verify command:**
```powershell
# Check syntax bằng Next.js dev compile (background)
cd apps\web
pnpm dev 2>&1 | Select-String "Compiled"
```

**Expected output:** `Compiled /admin` xuất hiện (có thể cần đợi vài giây).

---

### Step 10: Tạo `apps/web/app/(admin)/admin/page.tsx`
**File:** `apps/web/app/(admin)/admin/page.tsx` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```typescript
import { IconUsers, IconChannels, IconBrain, IconShield } from '@/components/icons';

const STAT_CARDS = [
  {
    label: 'MRR (estimate)',
    value: '—',
    hint: 'Sum tier pricing × active users',
    icon: IconChannels,
  },
  {
    label: 'Active Users (24h)',
    value: '—',
    hint: 'Distinct users with jobs in 24h',
    icon: IconUsers,
  },
  {
    label: 'Jobs Today',
    value: '—',
    hint: 'Jobs created since 00:00 UTC',
    icon: IconBrain,
  },
  {
    label: 'Credits Spent Today',
    value: '—',
    hint: 'Sum credits_spent from credit_transactions',
    icon: IconShield,
  },
];

export default function AdminDashboardPage() {
  return (
    <div className="p-8 space-y-8 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-[var(--fg-secondary)] max-w-xl">
          Tổng quan hệ thống. Số liệu sẽ được kết nối với API ở phase 6.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {STAT_CARDS.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="relative glass-strong rounded-2xl p-5 overflow-hidden animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div
                aria-hidden
                className="pointer-events-none absolute -top-12 -right-12 h-32 w-32 rounded-full bg-[var(--brand-500)] opacity-15 blur-2xl"
              />
              <div className="relative flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                    {card.label}
                  </p>
                  <p className="text-3xl font-bold tabular-nums">{card.value}</p>
                  <p className="text-xs text-[var(--fg-tertiary)] mt-2">
                    {card.hint}
                  </p>
                </div>
                <div className="shrink-0 h-10 w-10 rounded-xl bg-[var(--brand-500)]/20 flex items-center justify-center text-[var(--brand-300)]">
                  <Icon size={18} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-2">Phase 5 — Foundation</h2>
        <ul className="text-sm text-[var(--fg-secondary)] space-y-1 list-disc list-inside">
          <li>Migration 0022 đã được áp dụng (role, audit_logs, RPCs)</li>
          <li>Backend RBAC: <code className="text-[var(--brand-300)]">require_admin</code> dependency</li>
          <li>Audit log service với auto-mask sẵn sàng</li>
          <li>Phase 6 sẽ wire số liệu thật + thêm User/Credit management</li>
        </ul>
      </div>
    </div>
  );
}
```

**Verify command:**
```powershell
# Sau khi dev server chạy
curl.exe -I http://localhost:3000/admin 2>&1 | Select-Object -First 5
```

**Expected output:** `HTTP/1.1 307` (redirect to /login nếu chưa login) HOẶC `HTTP/1.1 200` nếu đã login admin.

---

### Step 11: Update `.env.example`
**File:** `d:\appDK\.env.example`
**Vị trí:** Append cuối file.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.

**Code cần viết (APPEND cuối file):**
```
# Admin panel
ADMIN_ALLOWED_IPS=127.0.0.1,::1
```

**Verify command:**
```powershell
Get-Content .env.example | Select-String "ADMIN_ALLOWED_IPS"
```

**Expected output:** Dòng `ADMIN_ALLOWED_IPS=...` tồn tại.

---

### Step 12: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `backend-development`.

**Verify commands:**
```powershell
# 1) Python imports compile
cd d:\appDK
python -c "from apps.api.services.credit_manager import get_user_role, CreditManager; print('OK1')"
python -c "from apps.api.dependencies.admin import require_admin; print('OK2')"
python -c "from apps.api.services.audit import log_admin_action, _mask_value; print('OK3')"

# 2) Unit test không regress
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 3) Migration file syntax check (visual)
Get-Content ..\supabase\migrations\0022_admin_panel_foundation.sql | Measure-Object -Line

# 4) Frontend compile check
cd ..\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:**
- OK1, OK2, OK3 in ra
- 2 test PASSED (test_hold_succeeds, test_hold_insufficient_raises)
- Line count ≥ 80
- 0 errors TS

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`
- Ghi vào `BLOCKERS.md` với format:
  ```
  ## Step X failure
  - Verify command: ...
  - Expected: ...
  - Actual: ...
  - Hypothesized cause: ...
  ```

---

## Definition of Done cho Phase này
- File `supabase/migrations/0022_admin_panel_foundation.sql` tồn tại, ≥ 80 dòng, syntax OK.
- File `apps/api/dependencies/admin.py` tồn tại, import OK.
- File `apps/api/services/audit.py` tồn tại, import OK.
- File `apps/web/middleware.ts` tồn tại, TS compile 0 errors.
- File `apps/web/app/(admin)/layout.tsx` tồn tại, Next.js compile 0 errors.
- File `apps/web/app/(admin)/admin/page.tsx` tồn tại, render OK.
- File `.env.example` có dòng `ADMIN_ALLOWED_IPS`.
- **KHÔNG** có file nào trong `apps/api/routers/projects.py`, `apps/api/modules/voice/*`, `apps/web/app/(dashboard)/**` bị đụng.
- Unit test `test_credit_manager.py` vẫn PASSED.
