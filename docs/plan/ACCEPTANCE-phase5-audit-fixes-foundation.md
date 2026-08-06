# Tiêu chí Nghiệm thu (ACCEPTANCE): phase5-audit-fixes-foundation

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### Database (Migration 0022)
- [ ] File `supabase/migrations/0022_admin_panel_foundation.sql` tồn tại với ≥ 80 dòng.
- [ ] File chứa 2 lệnh `DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT)` và `DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT)`.
- [ ] File chứa 1 lệnh `ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user' CHECK (...)`.
- [ ] File chứa 6 columns mới: `role`, `max_assistants`, `banned_at`, `banned_reason`, `deleted_at`, `last_sign_in_at`.
- [ ] File chứa 1 lệnh `CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL`.
- [ ] File chứa `CREATE TABLE IF NOT EXISTS admin_audit_logs` với đầy đủ columns đã liệt kê trong MSEW.
- [ ] File chứa 2 `CREATE OR REPLACE FUNCTION`: `admin_adjust_credits` và `soft_delete_user`.
- [ ] File chứa DROP POLICY + CREATE POLICY mới cho bảng `transcripts` (scope theo assistant).

### Backend Python
- [ ] File `apps/api/services/credit_manager.py` có function module-level `get_user_role(user_id: str) -> str` ở SAU `import get_supabase_admin`.
- [ ] File `apps/api/dependencies/admin.py` tồn tại với function `require_admin`.
- [ ] `require_admin` có logic cache role 60 giây trong dict `_ROLE_CACHE`.
- [ ] `require_admin` raise `HTTPException(403, 'Admin only')` khi role không hợp lệ.
- [ ] File `apps/api/services/audit.py` tồn tại với function `log_admin_action`.
- [ ] Function `_mask_value` mask các key chứa regex `(key|token|secret|password|api_key)`.

### Frontend (Next.js)
- [ ] File `apps/web/middleware.ts` tồn tại với `matcher: ['/admin/:path*', '/api/admin/:path*']`.
- [ ] Middleware check `supabase.auth.getSession()` và `users.role`.
- [ ] Nếu không login → redirect `/login?next=/admin`.
- [ ] Nếu role không phải admin → redirect `/403`.
- [ ] File `apps/web/app/(admin)/layout.tsx` tồn tại với sidebar 240px và 8 nav items.
- [ ] Layout có badge hiển thị role admin hiện tại.
- [ ] File `apps/web/app/(admin)/admin/page.tsx` tồn tại với 4 stat cards.
- [ ] Mỗi stat card có label, value placeholder ("—"), hint, icon.

### Environment
- [ ] File `.env.example` có dòng `ADMIN_ALLOWED_IPS=127.0.0.1,::1`.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Backward compatibility:** KHÔNG file nào trong `apps/api/routers/projects.py`, `apps/api/modules/voice/*`, `apps/api/modules/transcript/engine.py` bị thay đổi.
- **Migration safety:** Tất cả DROP/ADD dùng `IF EXISTS` / `IF NOT EXISTS` (idempotent).
- **Security:**
  - `require_admin` không log user_id.
  - `_mask_value` test pass với `{'openai_key': 'sk-xxx', 'name': 'foo'}` → `{'openai_key': '***', 'name': 'foo'}`.
  - `admin_audit_logs` không có explicit policy → service_role only.
- **Performance:** Cache role 60s tránh N+1 query.

## 3. Mục tiêu Test Coverage
- Mức coverage yêu cầu tối thiểu: **N/A** (phase này chưa thêm unit test mới, chỉ đảm bảo existing test pass).
- File phải đạt coverage hiện tại: `apps/api/test_credit_manager.py` (2 tests PASSED).

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Apply migration (nếu có Supabase local)
```powershell
cd d:\appDK
supabase db reset --linked
# Hoặc nếu không có local DB, chỉ kiểm tra syntax SQL bằng cách đọc file
Get-Content supabase\migrations\0022_admin_panel_foundation.sql
```

### Bước 2: Verify Python imports
```powershell
cd d:\appDK
python -c "from apps.api.services.credit_manager import get_user_role; print('credit_manager OK')"
python -c "from apps.api.dependencies.admin import require_admin; print('admin dep OK')"
python -c "from apps.api.services.audit import log_admin_action, _mask_value; print('audit OK')"
```

### Bước 3: Run existing unit test
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```

### Bước 4: Verify mask helper logic
```powershell
python -c "from apps.api.services.audit import _mask_value; r = _mask_value({'openai_key': 'sk-xxx', 'name': 'foo', 'deep': {'token': 't'}}); print(r)"
```
**Expected:** `{'openai_key': '***', 'name': 'foo', 'deep': {'token': '***'}}`

### Bước 5: Start dev server và test /admin
```powershell
cd d:\appDK\apps\web
pnpm dev
```
Trong browser: truy cập `http://localhost:3000/admin`
- **Nếu chưa login:** redirect đến `/login?next=/admin`
- **Nếu login với user thường:** redirect đến `/403`
- **Nếu login với admin:** hiển thị dashboard với 4 stat cards

### Bước 6: Verify TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** Không có output error.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 12 MSEW step phải PASS verify command của riêng nó, VÀ toàn bộ 4 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase5-audit-fixes-foundation.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.
