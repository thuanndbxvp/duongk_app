# Tiêu chí Nghiệm thu (ACCEPTANCE): phase6-admin-user-credit

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `apps/api/routers/admin_users.py` (NEW)
- [ ] File tồn tại, import OK.
- [ ] Có 9 endpoints:
  - `GET /api/admin/users` (list + filter + pagination)
  - `GET /api/admin/users/{user_id}` (detail + counts inline)
  - `POST /api/admin/users` (create user + audit log)
  - `PATCH /api/admin/users/{user_id}` (update + before/after audit)
  - `DELETE /api/admin/users/{user_id}` (soft delete via RPC)
  - `POST /api/admin/users/{user_id}/restore`
  - `POST /api/admin/users/{user_id}/ban` (reason ≥ 10 chars)
  - `POST /api/admin/users/{user_id}/unban`
  - `POST /api/admin/users/{user_id}/impersonate` (stub token, audit ghi rõ)
  - `POST /api/admin/users/{user_id}/adjust-credit` (RPC `admin_adjust_credits`, delta -10000..10000)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Mọi mutation có `log_admin_action()` call.
- [ ] Impersonate return `expires_at` ISO timestamp.

### File 2: `apps/api/routers/admin_credit.py` (NEW)
- [ ] File tồn tại, import OK.
- [ ] Có 4 endpoints:
  - `GET /api/admin/credit/ledger` (filter + pagination, count)
  - `GET /api/admin/credit/stats` (4 metrics + sparkline 7 ngày)
  - `GET /api/admin/credit/export` (CSV, max 50k rows, date range)
  - `GET /api/admin/credit/pricing` (list tất cả `credit_pricing`, không filter enabled)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Export trả về `Content-Type: text/csv` + `Content-Disposition: attachment`.
- [ ] CSV header: `tx_id, user_email, action, amount, balance_after, reason, created_at`.

### File 3: `apps/api/routers/admin_pricing.py` (NEW)
- [ ] File tồn tại, import OK.
- [ ] Có 2 endpoints:
  - `PATCH /api/admin/pricing/{job_type}` (update row + audit)
  - `POST /api/admin/pricing/reload` (stub — Phase 7+ impl Redis pub/sub)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Mọi mutation có `log_admin_action()` call.

### File 4: `apps/api/main.py` (UPDATE)
- [ ] Có 3 import mới: `admin_users_router`, `admin_credit_router`, `admin_pricing_router`.
- [ ] Có 3 `app.include_router(...)` cho admin.
- [ ] FastAPI app khởi động OK.
- [ ] Route list có ≥ 15 admin routes.

### File 5-8: Web proxy routes (4 NEW)
- [ ] `apps/web/app/api/admin/users/route.ts` (GET + POST).
- [ ] `apps/web/app/api/admin/users/[id]/route.ts` (GET + PATCH).
- [ ] `apps/web/app/api/admin/users/[id]/adjust-credit/route.ts` (POST).
- [ ] `apps/web/app/api/admin/credits/ledger/route.ts` (GET).
- [ ] TS compile 0 errors.

### File 9: `apps/web/app/(admin)/admin/users/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Có filter bar (search email, tier, status).
- [ ] Có table với 7 columns (Email, Name, Tier, Credits, Role, Status, Joined).
- [ ] Có pagination (Previous/Next).
- [ ] Click email row → navigate tới `/admin/users/[id]`.
- [ ] Loading state hiển thị "Loading…".
- [ ] Empty state hiển thị "No users".

### File 10: `apps/web/app/(admin)/admin/users/[id]/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Có 3 cards (Profile, Stats, Actions).
- [ ] Có form "Adjust Credit" với 2 inputs (delta + reason).
- [ ] Có button "Ban User" / "Unban User" toggle theo `user.banned_at`.
- [ ] Validation: reason ≥ 10 ký tự (client-side).
- [ ] Refresh user sau adjust.

### File 11: `apps/web/app/(admin)/admin/credits/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Có 4 stat cards (Total Issued/Spent/Hold/Refunded).
- [ ] Có button "Export CSV" → trigger download.
- [ ] Có table với 6 columns (User, Action, Amount, Balance After, Reason, Date).
- [ ] Amount màu xanh (positive) / đỏ (negative).

### File 12: `apps/web/app/(admin)/layout.tsx` (UPDATE)
- [ ] `Users.enabled = true` (line 9).
- [ ] `Credits.enabled = true` (line 10).
- [ ] 6 mục còn lại (Pricing, API Keys, Routing, Alerts, Audit Logs) KHÔNG đổi.
- [ ] Layout structure KHÔNG đổi.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Security:**
  - Mọi endpoint admin có `Depends(require_admin)`.
  - Mọi mutation có `log_admin_action()` với before/after snapshot.
  - Audit log tự mask field `*key*`, `*secret*`, `*token*`, `*password*` (Phase 5 đã implement).
- **Backward compatibility:**
  - 0 regression trên user-facing routes.
  - Phase 5 files (`require_admin`, `audit.py`, migration 0022) KHÔNG bị đụng.
- **No new dependency:** Không cài package mới.
- **Performance:**
  - User list query có pagination (max 50/trang).
  - Export CSV cap 50k rows.
  - Stats query giới hạn 90 ngày (`gte('created_at', 'now()-interval \'90 days\')`).

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 6 KHÔNG thêm unit test mới. Verify qua smoke test.
- **Frontend:** TS compile 0 errors là tiêu chí chính.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify Python imports + FastAPI app load
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.routers.admin_users import router; print('admin_users OK')"
python -c "from apps.api.routers.admin_credit import router; print('admin_credit OK')"
python -c "from apps.api.routers.admin_pricing import router; print('admin_pricing OK')"
```
**Expected:** 4 dòng "OK".

### Bước 2: List admin routes
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path]); print(len(routes), 'admin routes'); [print(r) for r in routes]"
```
**Expected:** ≥ 15 admin routes.

### Bước 3: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 4: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 5: Verify 3 trang admin tồn tại
```powershell
Test-Path "app\(admin)\admin\users\page.tsx"
Test-Path "app\(admin)\admin\users\[id]\page.tsx"
Test-Path "app\(admin)\admin\credits\page.tsx"
```
**Expected:** 3 True.

### Bước 6: Verify sidebar update
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "Users.*enabled.*true|Credits.*enabled.*true"
```
**Expected:** 2 matches.

### Bước 7: Visual smoke test (optional, cần browser + admin role)
```powershell
cd d:\appDK\apps\web
pnpm dev
```
Mở browser với admin user:
- `/admin` → Dashboard (Phase 5 stub) — KHÔNG đổi.
- `/admin/users` → User list table với data thật (nếu có users trong DB).
- Click vào 1 user → `/admin/users/[id]` → Profile + Stats + Actions cards.
- `/admin/credits` → 4 stat cards + ledger table + Export CSV button.
- Sidebar: "Users" + "Credits" không còn badge "Soon".

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 11 MSEW step phải PASS verify command của riêng nó, VÀ 7 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase6-admin-user-credit.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Sprint A3)
- **API Keys CRUD** (`/api/admin/api-keys`) — Phase 7+.
- **Routing Config** (`/api/admin/routing-config`) — Phase 8+.
- **Audit Log Viewer** (`/admin/audit-logs`) — Phase 9+.
- **Alerts** (`/admin/alerts`) — Phase 9+.
- **Impersonate JWT signing thật** — Phase 7+.
- **Soft-delete cron** (xoá user > 7 ngày deleted) — Phase 7+.