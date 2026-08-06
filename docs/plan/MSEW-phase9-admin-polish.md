# MSEW: phase9-admin-polish

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase9-admin-polish.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase9-admin-polish.md`
- **Phase 5/6/7/8 đã xong:** admin routers + audit + key_resolver + vault + routing + config_watcher.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Service `ip_whitelist.py` | `backend-development` | `devops` | `debugging` |
| 2 | Service `backup.py` | `backend-development` | `database-admin` | `debugging` |
| 3 | Router `admin_audit.py` | `backend-development` | `better-auth` | `database-admin` |
| 4 | Wire `embedder.py` | `backend-development` | `code-review` | `debugging` |
| 5 | Wire `script_generate.py` | `backend-development` | `code-review` | `debugging` |
| 6 | UPDATE `main.py` | `backend-development` | `debugging` | `code-review` |
| 7 | 2 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 8 | UI `audit-logs/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 9 | UPDATE `layout.tsx` | `frontend-development` | `ui-styling` | `debugging` |
| 10 | Doc `admin_handbook.md` | `docs-manager` | `code-review` | `debugging` |
| 11 | Self-verify | `debugging` | `code-review` | `devops` |

## Files KHÔNG được đụng (Do Not Touch)
- Phase 5/6/7/8 files (admin routers, audit, key_resolver, vault, routing, config_watcher).
- User-facing routes.
- Worker task files KHÔNG thuộc wire (analysis_task, idea_generate, collect_channel, scene_breakdown).
- `transcript/engine.py`, `voice/routes.py`, `analysis_task.py` (Phase 8 đã wire đủ — Phase 9 KHÔNG đụng).
- MFA / TOTP / analytics / ffmpeg dispatcher / thumbnail_vision (Phase 10+).

---

## Micro-Steps

### Step 1: Tạo `apps/api/services/ip_whitelist.py`
**File:** `apps/api/services/ip_whitelist.py` (NEW)
**Vai trò:** FastAPI middleware check IP CIDR.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `devops`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
IP whitelist middleware — chỉ áp dụng cho /api/admin/**.
Config qua env ADMIN_ALLOWED_IPS (comma-separated CIDR).
Empty = allow all (dev mode).
"""
import ipaddress
import os
from typing import List
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def _load_allowed_networks() -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse env ADMIN_ALLOWED_IPS thành list network objects."""
    raw = os.environ.get('ADMIN_ALLOWED_IPS', '').strip()
    if not raw:
        return []  # Empty = allow all
    
    networks = []
    for cidr in raw.split(','):
        cidr = cidr.strip()
        if not cidr:
            continue
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            # Log warning nhưng không fail
            import logging
            logging.warning(f'[ip_whitelist] Invalid CIDR: {cidr}')
    
    return networks


def _ip_matches(client_ip: str, networks: List) -> bool:
    """Check client_ip có thuộc 1 trong networks không."""
    if not networks:
        return True  # Empty whitelist = allow all
    
    try:
        ip = ipaddress.ip_address(client_ip)
        return any(ip in net for net in networks)
    except ValueError:
        return False


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware block request từ IP không thuộc ADMIN_ALLOWED_IPS.
    CHỉ áp dụng cho paths bắt đầu /api/admin/.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Chỉ check admin routes
        if not request.url.path.startswith('/api/admin/'):
            return await call_next(request)
        
        # Lấy client IP (FastAPI default — không trust X-Forwarded-For)
        client_ip = request.client.host if request.client else 'unknown'
        
        # Parse whitelist (lazy — re-parse mỗi request hoặc cache 60s)
        networks = _load_allowed_networks()
        
        if not _ip_matches(client_ip, networks):
            return JSONResponse(
                status_code=403,
                content={'detail': f'IP {client_ip} not in admin whitelist'},
            )
        
        return await call_next(request)


def is_ip_allowed(client_ip: str) -> bool:
    """Helper test ngoài middleware."""
    return _ip_matches(client_ip, _load_allowed_networks())
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.services.ip_whitelist import IPWhitelistMiddleware, is_ip_allowed; print('ip_whitelist OK')"
```

**Expected output:** `ip_whitelist OK`.

---

### Step 2: Tạo `apps/api/services/backup.py`
**File:** `apps/api/services/backup.py` (NEW)
**Vai trò:** Helper dump/restore config JSON (3 tables).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Backup/restore config — dump metadata của 3 tables sang JSON.
KHÔNG dump encrypted_value (security).
"""
import json
from datetime import datetime, timezone
from typing import Optional
from apps.api.dependencies.supabase import get_supabase_admin


CONFIG_TABLES = [
    {
        'name': 'service_routing_config',
        'select': 'id, feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd, config_version',
    },
    {
        'name': 'credit_pricing',
        'select': 'job_type, credits, description, enabled',
    },
    {
        'name': 'api_provider_keys',
        # Exclude encrypted_value — security
        'select': 'id, provider, label, is_active, rate_limit_rpm, monthly_budget_usd, expires_at, archived_at',
    },
]


def dump_config() -> dict:
    """
    Dump tất cả config tables thành dict (KHÔNG bao gồm secrets).
    Returns: {'timestamp': ISO, 'tables': {table_name: [rows]}}
    """
    db = get_supabase_admin()
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0',
        'tables': {},
    }
    
    for table in CONFIG_TABLES:
        result = db.table(table['name']).select(table['select']).execute()
        output['tables'][table['name']] = result.data or []
    
    return output


def restore_config(config_data: dict, dry_run: bool = True) -> dict:
    """
    Restore config từ dict. dry_run=True (default) chỉ report, không apply.
    Returns: {'restored': N, 'errors': [msgs], 'dry_run': bool}
    """
    if dry_run:
        return {
            'dry_run': True,
            'restored': 0,
            'errors': [],
            'would_update': sum(len(v) for v in config_data.get('tables', {}).values()),
        }
    
    db = get_supabase_admin()
    errors = []
    restored = 0
    
    for table_name, rows in config_data.get('tables', {}).items():
        for row in rows:
            try:
                # Upsert by primary key (id) hoặc (job_type) cho credit_pricing
                if 'id' in row:
                    db.table(table_name).upsert(row).execute()
                elif 'job_type' in row:
                    db.table(table_name).upsert(row, on_conflict='job_type').execute()
                restored += 1
            except Exception as e:
                errors.append(f'{table_name}: {e}')
    
    return {
        'dry_run': False,
        'restored': restored,
        'errors': errors,
    }


def export_to_file(filepath: str) -> str:
    """Dump config → JSON file. Return file path."""
    config = dump_config()
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    return filepath
```

**Verify command:**
```powershell
python -c "from apps.api.services.backup import dump_config, restore_config, export_to_file; print('backup OK')"
```

**Expected output:** `backup OK`.

---

### Step 3: Tạo `apps/api/routers/admin_audit.py`
**File:** `apps/api/routers/admin_audit.py` (NEW)
**Vai trò:** 3 endpoints (list, detail, export CSV).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `database-admin`.

**Code cần viết:**
```python
"""
Admin Audit Log Viewer — 3 endpoints (read-only).
Mounted dưới /api/admin/audit-logs.
"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Optional
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/admin/audit-logs", tags=["Admin Audit Logs"])


@router.get("")
async def list_audit_logs(
    admin_id: str = Depends(require_admin),
    admin_email: Optional[str] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """
    List audit logs với filter + full-text search (via admin_email/action/target_id).
    """
    db = get_supabase_admin()
    query = db.table('admin_audit_logs').select('*', count='exact')
    
    if admin_email:
        query = query.ilike('admin_email', f'%{admin_email}%')
    if action:
        query = query.ilike('action', f'%{action}%')
    if target_type:
        query = query.eq('target_type', target_type)
    if target_id:
        query = query.ilike('target_id', f'%{target_id}%')
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    return {
        'logs': result.data or [],
        'total': result.count or 0,
        'page': page,
        'limit': limit,
    }


@router.get("/{log_id}")
async def get_audit_log(
    log_id: str,
    admin_id: str = Depends(require_admin),
):
    """Lấy chi tiết 1 audit log (xem before/after JSON đã masked)."""
    db = get_supabase_admin()
    result = db.table('admin_audit_logs').select('*').eq('id', log_id).single().execute()
    if not result.data:
        raise HTTPException(404, 'Audit log not found')
    return result.data


@router.get("/export/csv")
async def export_audit_csv(
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Export audit log → CSV. Cap 10k rows."""
    db = get_supabase_admin()
    
    if not from_date or not to_date:
        raise HTTPException(400, 'from_date and to_date required (max 30 days range)')
    
    # Validate date range
    try:
        from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        if (to_dt - from_dt).days > 30:
            raise HTTPException(400, 'Date range max 30 days')
    except ValueError:
        raise HTTPException(400, 'Invalid date format (use ISO 8601)')
    
    query = (
        db.table('admin_audit_logs')
        .select('id, admin_email, action, target_type, target_id, ip, user_agent, reason, created_at')
        .gte('created_at', from_date)
        .lte('created_at', to_date)
        .order('created_at', desc=True)
        .limit(10000)
    )
    result = query.execute()
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'admin_email', 'action', 'target_type', 'target_id', 'ip', 'user_agent', 'reason', 'created_at'])
    for row in (result.data or []):
        writer.writerow([
            row['id'], row['admin_email'], row['action'], row['target_type'],
            row['target_id'], row.get('ip'), row.get('user_agent'),
            row.get('reason'), row['created_at'],
        ])
    
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="admin-audit-logs.csv"'},
    )
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_audit import router; print('admin_audit OK')"
```

**Expected output:** `admin_audit OK`.

---

### Step 4: Wire `apps/api/modules/rag/embedder.py` (Phase 8 stub → fully wired)
**File:** `apps/api/modules/rag/embedder.py` (UPDATE — modify `embed_texts`)
**Vị trí:** Method `embed_texts` (line 11).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Modify method `embed_texts` (line 11-21)**, thay thế:
```python
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with auto-routing + Phase 8 config-driven provider."""
        if not texts:
            return []
        
        provider = self._select_embedding_provider()
        lang = self.router.detect_language(texts[0])
        model, dims, _ = self.router.get_model_config(lang)
        
        # Phase 9 wire: nếu provider từ routing khác default → dùng provider đó
        if provider == 'cohere':
            return await self._embed_cohere(texts, model)
        if provider == 'openai':
            return await self._embed_openai(texts, model, dims)
        
        # Fallback về router default
        if lang in ('vi', 'zh'):
            return await self._embed_cohere(texts, model)
        return await self._embed_openai(texts, model, dims)
```

**KHÔNG sửa:**
- `_embed_cohere` + `_embed_openai` methods.
- Class structure.

**Verify command:**
```powershell
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder wired OK')"
```

**Expected output:** `embedder wired OK`.

---

### Step 5: Wire `apps/worker/tasks/script_generate.py` (Phase 8 stub → fully wired)
**File:** `apps/worker/tasks/script_generate.py` (UPDATE — modify `generate_script`)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Modify function `generate_script`** (tìm function chính), thêm routing check trước khi gọi OpenAI:
```python
def generate_script(...):
    # ... existing code ...
    
    # Phase 9 wire: select LLM provider từ routing
    from apps.api.services.routing import get_routing_config
    routing = get_routing_config('llm_text')
    provider = routing.get('primary_provider', 'openai')
    
    if provider == 'openai':
        # existing OpenAI call
        response = openai_client.chat.completions.create(...)
    elif provider == 'stali':
        # Phase 10+ implement
        response = openai_client.chat.completions.create(...)  # fallback OpenAI
    else:
        # fallback cứng
        response = openai_client.chat.completions.create(...)
    
    # ... rest of function ...
```

**Lưu ý:** Phase 9 chỉ wire logic routing check, KHÔNG implement provider `stali`. Nếu primary != openai → vẫn dùng openai (fallback). Phase 10+ implement `stali`.

**Verify command:**
```powershell
python -c "from apps.worker.tasks.script_generate import generate_script; print('script_generate wired OK')"
```

**Expected output:** `script_generate wired OK`.

---

### Step 6: UPDATE `apps/api/main.py` register middleware + audit router
**File:** `apps/api/main.py` (UPDATE)
**Vị trí:** Sau Phase 8 admin imports + mounts.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** Phase 8 admin imports, **THÊM:**
```python
from apps.api.services.ip_whitelist import IPWhitelistMiddleware
from apps.api.routers.admin_audit import router as admin_audit_router
```

**SAU** `app = FastAPI(...)` (sau khi tạo app), **THÊM:**
```python
# Register IP whitelist middleware (Phase 9)
app.add_middleware(IPWhitelistMiddleware)
```

**SAU** Phase 8 admin mounts, **THÊM:**
```python
app.include_router(admin_audit_router)
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'audit' in r.path]; print(len(routes), 'audit routes'); [print(r) for r in sorted(routes)]"
```

**Expected output:** ≥ 3 routes (list + detail + export).

---

### Step 7: Tạo 2 web proxy routes
**Files (2 NEW):**
- `apps/web/app/api/admin/audit-logs/route.ts`
- `apps/web/app/api/admin/audit-logs/[id]/route.ts`
- `apps/web/app/api/admin/audit-logs/export/csv/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Pattern lặp lại:**

**`apps/web/app/api/admin/audit-logs/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/audit-logs${params ? `?${params}` : ''}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/audit-logs/[id]/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  try {
    const response = await apiFetch(`/api/admin/audit-logs/${id}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/audit-logs/export/csv/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/audit-logs/export/csv${params ? `?${params}` : ''}`, {}, token);
    const blob = await response.blob();
    return new NextResponse(blob, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'text/csv',
        'Content-Disposition': response.headers.get('Content-Disposition') || 'attachment',
      },
    });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 8: Tạo `apps/web/app/(admin)/admin/audit-logs/page.tsx`
**File:** `apps/web/app/(admin)/admin/audit-logs/page.tsx` (NEW)
**Vai trò:** Audit log table + filter + JSON diff modal.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

interface AuditLog {
  id: string;
  admin_email: string;
  action: string;
  target_type: string;
  target_id: string | null;
  before: Record<string, any> | null;
  after: Record<string, any> | null;
  ip: string | null;
  user_agent: string | null;
  reason: string | null;
  created_at: string;
}

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [targetFilter, setTargetFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [page, actionFilter, targetFilter, emailFilter]);

  function loadLogs() {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), limit: '50' });
    if (actionFilter) params.set('action', actionFilter);
    if (targetFilter) params.set('target_type', targetFilter);
    if (emailFilter) params.set('admin_email', emailFilter);

    fetch(`/api/admin/audit-logs?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      })
      .finally(() => setLoading(false));
  }

  async function openDetail(id: string) {
    const res = await fetch(`/api/admin/audit-logs/${id}`);
    if (res.ok) setSelectedLog(await res.json());
  }

  function handleExport() {
    const from = prompt('From date (YYYY-MM-DD):');
    if (!from) return;
    const to = prompt('To date (YYYY-MM-DD, max 30 days from from):');
    if (!to) return;
    window.location.href = `/api/admin/audit-logs/export/csv?from_date=${from}T00:00:00Z&to_date=${to}T23:59:59Z`;
  }

  const totalPages = Math.ceil(total / 50);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Audit Logs</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{total} entries</p>
      </div>

      {/* Filters */}
      <div className="glass rounded-2xl p-4 flex flex-wrap gap-3">
        <input
          type="text" placeholder="Admin email…"
          value={emailFilter} onChange={(e) => { setEmailFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <input
          type="text" placeholder="Action (vd: user.update)…"
          value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <input
          type="text" placeholder="Target type (vd: user)…"
          value={targetFilter} onChange={(e) => { setTargetFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <button
          onClick={handleExport}
          className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Admin</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Action</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Target</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Reason</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">Loading…</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">No logs</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id} onClick={() => openDetail(log.id)}
                className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)] cursor-pointer">
                <td className="px-4 py-3 text-[var(--brand-300)]">{log.admin_email}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {log.target_type}/{log.target_id?.slice(0, 12)}…
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)] max-w-xs truncate">
                  {log.reason || '—'}
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {new Date(log.created_at).toLocaleString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button disabled={page === 1} onClick={() => setPage(page - 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30">
            ← Previous
          </button>
          <span className="text-sm text-[var(--fg-tertiary)]">Page {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(page + 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30">
            Next →
          </button>
        </div>
      )}

      {/* JSON Diff Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
          onClick={() => setSelectedLog(null)}>
          <div className="glass-strong rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedLog.action}</h2>
                <p className="text-sm text-[var(--fg-tertiary)]">
                  {selectedLog.admin_email} · {new Date(selectedLog.created_at).toLocaleString('vi-VN')}
                </p>
              </div>
              <button onClick={() => setSelectedLog(null)}
                className="text-2xl text-[var(--fg-tertiary)] hover:text-white">×</button>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold mb-2 text-red-400">Before</h3>
                <pre className="text-xs bg-[var(--surface)] rounded p-3 overflow-x-auto max-h-96">
                  {JSON.stringify(selectedLog.before, null, 2) || 'null'}
                </pre>
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-2 text-green-400">After</h3>
                <pre className="text-xs bg-[var(--surface)] rounded p-3 overflow-x-auto max-h-96">
                  {JSON.stringify(selectedLog.after, null, 2) || 'null'}
                </pre>
              </div>
            </div>
            {selectedLog.reason && (
              <div className="mt-4 text-sm">
                <strong>Reason:</strong> {selectedLog.reason}
              </div>
            )}
            <div className="mt-4 text-xs text-[var(--fg-tertiary)]">
              IP: {selectedLog.ip || '—'} · UA: {selectedLog.user_agent?.slice(0, 50) || '—'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 9: UPDATE `apps/web/app/(admin)/layout.tsx` enable Audit Logs
**File:** `apps/web/app/(admin)/layout.tsx` (UPDATE)
**Vị trí:** Line 15 (`Audit Logs`).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Code cần viết (1 lần `StrReplace`):**

**Thay — line 15:**
```typescript
  { href: '/admin/audit-logs', label: 'Audit Logs', icon: IconShield, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/audit-logs', label: 'Audit Logs', icon: IconShield, enabled: true },
```

**KHÔNG được sửa:**
- 7 mục còn lại (Dashboard, Users, Credits, Pricing, API Keys, Routing, Alerts).
- Layout structure.

**Verify command:**
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "enabled:" | Measure-Object -Line
```

**Expected output:** 8 lines.

---

### Step 10: Tạo `docs/admin_handbook.md`
**File:** `docs/admin_handbook.md` (NEW)
**Vai trò:** Hướng dẫn sử dụng admin panel — song ngữ VI/EN.
**Skill Invocation:**
  - **Primary:** `docs-manager`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```markdown
# Admin Panel Handbook — AppDK
> Cập nhật: 2026-08-06 · Phiên bản: 1.0 · Tác giả: Admin Team

## Giới thiệu / Introduction

Admin Panel là công cụ quản trị hệ thống AppDK, cho phép admin:
- Quản lý users (CRUD, ban, soft-delete, impersonate).
- Điều chỉnh credits (adjust + ledger + export).
- Quản lý API keys providers (OpenAI, Cohere, R2, Modal, ...) với encryption.
- Cấu hình routing 8 nghiệp vụ (transcript, TTS, embedding, ...) với hot-reload.
- Xem audit log + IP whitelist.

The Admin Panel manages AppDK system, allowing admins to manage users, credits, API keys, service routing, and audit logs.

## Truy cập / Access

1. **URL:** `https://app.example.com/admin`
2. **Yêu cầu / Requirements:**
   - User có `role = admin` hoặc `super_admin` trong bảng `users`.
   - IP phải thuộc `ADMIN_ALLOWED_IPS` (CIDR list, comma-separated).
   - 2FA (Phase 10+, hiện tại chỉ cần password).

## Cấu trúc Sidebar / Sidebar Structure

| Menu | Mục đích | Phase |
|------|----------|-------|
| Dashboard | Tổng quan hệ thống (4 stat cards) | 5 |
| Users | List, search, filter, detail, adjust credit, ban, impersonate | 6 |
| Credits | Ledger toàn hệ thống + stats + export CSV | 6 |
| Pricing | CRUD credit_pricing (per job_type) | 6 |
| API Keys | CRUD providers + encrypt + rotate + test | 7 |
| Routing | 8 features × primary + fallback + cost | 8 |
| Alerts | List unresolved budget/error alerts | 7 |
| Audit Logs | Full-text search + JSON diff + export | 9 |

## Tasks thường gặp / Common Tasks

### 1. Adjust credit cho user / Adjust User Credit
```
1. Vào /admin/users → search email user → click row
2. Tab "Profile" → thấy credit balance hiện tại
3. Form "Adjust Credit" → nhập delta (+/-) + lý do (≥ 10 ký tự)
4. Click "Adjust Credit" → balance update + audit log ghi
```

### 2. Rotate API key / Rotate API Key
```
1. Vào /admin/api-keys → tìm provider → click "Rotate"
2. Nhập new value → confirm
3. Key cũ archive (giữ 7 ngày), key mới active
4. Worker tự động reload cache trong < 60s
```

### 3. Đổi primary provider cho TTS / Change TTS Provider
```
1. Vào /admin/routing → tìm card "Text-to-Speech"
2. Dropdown "Primary" → chọn provider mới
3. Click "Save + Hot Reload"
4. Job TTS mới dùng provider mới trong < 60s (worker pick up qua Redis pub/sub)
```

### 4. Xem audit log / View Audit Logs
```
1. Vào /admin/audit-logs → filter theo admin_email / action / target
2. Click row → modal hiển thị JSON diff (before vs after)
3. Click "Export CSV" → download file (date range max 30 ngày)
```

## Security / Bảo mật

- **Audit log:** Mọi mutation đều ghi vào `admin_audit_logs`. Field sensitive (`*key*`, `*secret*`, `*token*`, `*password*`) tự động mask thành `***`.
- **IP Whitelist:** Set env `ADMIN_ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8`. Empty = allow all (DEV ONLY).
- **Encryption:** API key values lưu encrypted bằng Fernet (AES-128-CBC + HMAC). Key từ env `ENCRYPTION_KEY`.
- **Rate limit:** Áp dụng ở Caddy (recommended) hoặc Cloudflare.

## Troubleshooting

### Lỗi 403 khi truy cập /admin
- Check role user trong DB: `SELECT email, role FROM users WHERE email = '<your-email>';`
- Nếu `role = user` → update thành `admin` hoặc `super_admin`.

### API key test fail / API Key Test Failed
- Check key còn valid không (provider dashboard).
- Check budget có bị exhausted không (`/admin/api-keys` → cột `Cost (mo)`).
- Check rate limit (provider dashboard).

### Routing config thay đổi không có hiệu lực
- Click "Reload" trên card `/admin/routing`.
- Hoặc đợi 60s (worker polling fallback).
- Check worker logs: `[config_watcher] Routing config updated for feature: <feature>`.

### Audit log ghi sai before/after
- Phase 5 audit mask đã sẵn. Kiểm tra `_SENSITIVE_KEYS` regex ở `apps/api/services/audit.py`.

## Phase Roadmap (đã xong + sắp tới)

| Phase | Tính năng | Status |
|-------|-----------|--------|
| 5 | Foundation (RBAC, audit log, RPCs) | ✅ Done |
| 6 | User & Credit Management | ✅ Plan |
| 7 | API Keys (encryption + rotate) | ✅ Plan |
| 8 | Service Routing (hot-reload) | ✅ Plan |
| 9 | Polish (audit log viewer, IP whitelist, docs) | ✅ Plan |
| 10+ | 2FA TOTP, analytics, backup cron, ffmpeg dispatcher | 📋 Future |

## Liên hệ / Contact

- Slack: #admin-panel channel
- Email: admin@appdk.example.com
- On-call: PagerDuty rotation

---

> **Lưu ý quan trọng / Important:**
> - KHÔNG commit secret thật vào repo. Dùng env vars.
> - KHÔNG share admin JWT. Mỗi admin có session riêng.
> - KHÔNG disable audit log. Mọi mutation PHẢI được log.
> - DO NOT commit real secrets. Use env vars.
> - DO NOT share admin JWT. Each admin has own session.
> - DO NOT disable audit log. All mutations MUST be logged.
```

**Verify command:**
```powershell
Test-Path "d:\appDK\docs\admin_handbook.md"
```

**Expected output:** True.

---

### Step 11: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `devops`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) All Python imports
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.ip_whitelist import IPWhitelistMiddleware, is_ip_allowed; print('ip_whitelist OK')"
python -c "from apps.api.services.backup import dump_config, restore_config, export_to_file; print('backup OK')"
python -c "from apps.api.routers.admin_audit import router; print('admin_audit OK')"
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder wired OK')"
python -c "from apps.worker.tasks.script_generate import generate_script; print('script_generate wired OK')"

# 2) Admin audit routes count
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'audit' in r.path]; print(len(routes), 'audit routes')"

# 3) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 4) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 5) UI page + docs exists
Test-Path "app\(admin)\admin\audit-logs\page.tsx"
Test-Path "..\docs\admin_handbook.md"

# 6) IP whitelist test (dev mode = allow all)
$env:ADMIN_ALLOWED_IPS = ""
python -c "from apps.api.services.ip_whitelist import is_ip_allowed; print('allow all:', is_ip_allowed('1.2.3.4'))"

# 7) IP whitelist test (with CIDR)
$env:ADMIN_ALLOWED_IPS = "192.168.1.0/24"
python -c "from apps.api.services.ip_whitelist import is_ip_allowed; print('192.168.1.5:', is_ip_allowed('192.168.1.5')); print('10.0.0.1:', is_ip_allowed('10.0.0.1'))"
```

**Expected output:**
- 6 dòng "OK"
- 3 audit routes
- 2 tests PASSED
- 0 errors TS
- 1 UI page + 1 docs = True
- IP whitelist logic đúng

---

## Definition of Done cho Phase này
- 2 service mới (`ip_whitelist`, `backup`).
- 1 router admin (`admin_audit` với 3 endpoints).
- 1 middleware IP whitelist registered trong `main.py`.
- 2 consumer wire (`embedder`, `script_generate`).
- 3 web proxy routes + 1 trang admin (`/admin/audit-logs`).
- Sidebar enable Audit Logs (line 15).
- 1 doc handbook (`docs/admin_handbook.md`).
- TS compile 0 errors.
- Existing pytest PASSED.
- IP whitelist test: dev mode allow all, prod mode filter CIDR đúng.
- Audit log viewer: filter + JSON diff + export CSV hoạt động.
- KHÔNG file nào trong Phase 5/6/7/8 bị đụng ngoài `main.py` (chỉ thêm middleware + mount router) + `layout.tsx` (enable sidebar).