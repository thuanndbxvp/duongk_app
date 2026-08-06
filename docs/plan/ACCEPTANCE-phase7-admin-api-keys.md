# Tiêu chí Nghiệm thu (ACCEPTANCE): phase7-admin-api-keys

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1-3: Migrations (3 NEW)
- [ ] `supabase/migrations/0023_api_provider_keys.sql` có bảng `api_provider_keys` với columns: `id`, `provider`, `label`, `encrypted_value BYTEA`, `is_active`, `rate_limit_rpm`, `monthly_budget_usd`, `current_month_cost_usd`, `last_used_at`, `last_tested_at`, `last_test_status`, `last_test_latency_ms`, `last_test_error`, `expires_at`, `created_by`, `created_at`, `updated_at`, `archived_at`.
- [ ] Có index `idx_apikeys_provider_active` + `idx_apikeys_archived`.
- [ ] RLS enabled, no explicit policy (default deny).
- [ ] `supabase/migrations/0024_api_usage_logs.sql` có bảng `api_usage_logs` + view `api_usage_summary`.
- [ ] `supabase/migrations/0025_admin_alerts.sql` có bảng `admin_alerts` + RPC `create_alert(severity, category, message, context)` (idempotent).
- [ ] Tất cả migrations áp dụng thành công không break schema cũ.

### File 4: `apps/api/services/vault.py` (NEW)
- [ ] Có hàm `encrypt(plaintext: str) → bytes`.
- [ ] Có hàm `decrypt(ciphertext: bytes) → str`.
- [ ] Có hàm `generate_key() → str` (44-char base64).
- [ ] Dùng Fernet (AES-128-CBC + HMAC SHA-256).
- [ ] Fallback: nếu `ENCRYPTION_KEY` chưa set, derive từ `SECRET_KEY` (hash SHA-256).
- [ ] Roundtrip OK: `decrypt(encrypt('test')) == 'test'`.

### File 5: `apps/api/services/key_resolver.py` (NEW)
- [ ] Có hàm `resolve_key(provider: str) → Optional[str]` với priority: env var → DB lookup.
- [ ] Cache 60s in-memory (thread-safe với `threading.Lock`).
- [ ] Có hàm `invalidate_cache(provider: Optional[str])`.
- [ ] Có hàm `get_active_keys_summary() → dict[provider, list[label]]` (chỉ labels, không value).

### File 6: `apps/api/services/usage_tracker.py` (NEW)
- [ ] Có decorator `@track_usage(provider, feature, cost_per_call_usd)`.
- [ ] Log vào `api_usage_logs` + update `current_month_cost_usd` (Phase 7 stub — không RPC reset).
- [ ] Tracking fail KHÔNG throw (best-effort).

### File 7: `apps/api/routers/admin_api_keys.py` (NEW)
- [ ] Có 7 endpoints:
  - `GET /api/admin/api-keys` (list, filter by provider, include_archived)
  - `POST /api/admin/api-keys` (create + encrypt)
  - `PATCH /api/admin/api-keys/{id}` (update metadata)
  - `POST /api/admin/api-keys/{id}/rotate` (archive old + insert new + invalidate cache)
  - `DELETE /api/admin/api-keys/{id}` (soft archive)
  - `POST /api/admin/api-keys/{id}/test` (decrypt + ping provider)
  - `GET /api/admin/api-keys/{id}/usage` (24h/7d/30d stats)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Mọi mutation gọi `log_admin_action()` (audit ghi before/after với mask).
- [ ] `_test_provider()` có case cho openai/cohere/modal/r2/supadata/serpapi/youtube/supabase_service_role.
- [ ] Test endpoint update `last_tested_at` + `last_test_status` + `last_test_latency_ms` + `last_test_error`.

### File 8: `apps/api/routers/admin_alerts.py` (NEW)
- [ ] Có 2 endpoints:
  - `GET /api/admin/alerts` (list, filter severity/category, include_resolved)
  - `POST /api/admin/alerts/{id}/resolve` (set resolved_at + resolved_by)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Resolve gọi `log_admin_action()`.

### File 9: `apps/api/main.py` (UPDATE)
- [ ] Có 2 import mới: `admin_api_keys_router`, `admin_alerts_router`.
- [ ] Có 2 `app.include_router(...)` mới.
- [ ] Admin route count ≥ 9 (7 api-keys + 2 alerts) MỚI (chưa tính Phase 6).

### File 10-15: Web proxy routes (6 NEW)
- [ ] `apps/web/app/api/admin/api-keys/route.ts` (GET + POST).
- [ ] `apps/web/app/api/admin/api-keys/[id]/route.ts` (PATCH + DELETE).
- [ ] `apps/web/app/api/admin/api-keys/[id]/test/route.ts` (POST).
- [ ] `apps/web/app/api/admin/api-keys/[id]/rotate/route.ts` (POST).
- [ ] `apps/web/app/api/admin/alerts/route.ts` (GET).
- [ ] `apps/web/app/api/admin/alerts/[id]/resolve/route.ts` (POST).
- [ ] TS compile 0 errors.

### File 16: `apps/web/app/(admin)/admin/api-keys/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Có form "Add Key" (provider dropdown + label + value + budget).
- [ ] Có accordion-style table group by provider.
- [ ] Mỗi row có nút Test + Rotate.
- [ ] Status badge (active/inactive/archived) với màu sắc rõ ràng.

### File 17: `apps/web/app/(admin)/admin/alerts/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Có toggle "Show resolved".
- [ ] Có severity badge (info/warning/critical) với màu sắc.
- [ ] Mỗi alert có button Resolve (chỉ hiện nếu chưa resolved).
- [ ] Empty state: "No alerts 🎉".

### File 18: `apps/web/app/(admin)/layout.tsx` (UPDATE)
- [ ] `API Keys.enabled = true` (line 12).
- [ ] `Alerts.enabled = true` (line 14).
- [ ] 4 mục còn lại (Dashboard, Users, Credits, Pricing, Routing, Audit Logs) KHÔNG đổi.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Security:**
  - Mọi endpoint admin có `Depends(require_admin)`.
  - `encrypted_value` LÀ BYTEA (hex-encoded). KHÔNG bao giờ return raw value qua API.
  - `list_keys` SELECT chỉ định columns (không có `encrypted_value`).
  - Test endpoint decrypt 1 lần in-memory, KHÔNG log raw value.
  - `ENCRYPTION_KEY` fallback SHA-256(SECRET_KEY) nếu chưa set (warning cho production).
- **Backward compatibility:**
  - 0 regression trên Phase 5/6 endpoints.
  - 0 regression trên user-facing routes.
  - `key_resolver` check env FIRST → nếu Phase 8+ chưa refactor worker, vẫn dùng `os.environ`.
- **No new dependency:**
  - `cryptography` (Fernet) cần cài.
  - `boto3` đã có (cho R2 test).
  - `openai`, `cohere`, `supabase`, `requests`, `googleapiclient` đã có.
- **Cache safety:**
  - Cache 60s → key rotate có thể stale tối đa 60s.
  - Phase 8+ sẽ thêm Redis pub/sub để invalidate ngay.

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 7 KHÔNG thêm unit test mới. Verify qua smoke test + manual UI test.
- **Frontend:** TS compile 0 errors.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify cryptography installed
```powershell
pip show cryptography
```
**Expected:** `Name: cryptography` + `Version: ...`.

### Bước 2: Verify Python imports
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.vault import encrypt, decrypt, generate_key; print('vault OK')"
python -c "from apps.api.services.key_resolver import resolve_key; print('key_resolver OK')"
python -c "from apps.api.services.usage_tracker import track_usage; print('usage_tracker OK')"
python -c "from apps.api.routers.admin_api_keys import router; print('admin_api_keys OK')"
python -c "from apps.api.routers.admin_alerts import router; print('admin_alerts OK')"
```
**Expected:** 6 dòng "OK".

### Bước 3: Verify Fernet roundtrip
```powershell
python -c "from apps.api.services.vault import encrypt, decrypt; assert decrypt(encrypt('test')) == 'test'; print('roundtrip OK')"
```
**Expected:** `roundtrip OK`.

### Bước 4: Verify admin routes count
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and ('api-keys' in r.path or 'alerts' in r.path)]); print(len(routes), 'new routes')"
```
**Expected:** `9 new routes`.

### Bước 5: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 6: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 7: Verify 3 migration files
```powershell
Test-Path "..\supabase\migrations\0023_api_provider_keys.sql"
Test-Path "..\supabase\migrations\0024_api_usage_logs.sql"
Test-Path "..\supabase\migrations\0025_admin_alerts.sql"
```
**Expected:** 3 True.

### Bước 8: Verify 2 trang admin tồn tại
```powershell
Test-Path "app\(admin)\admin\api-keys\page.tsx"
Test-Path "app\(admin)\admin\alerts\page.tsx"
```
**Expected:** 2 True.

### Bước 9: Verify sidebar update
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "API Keys.*enabled.*true|Alerts.*enabled.*true"
```
**Expected:** 2 matches.

### Bước 10: Visual smoke test (optional, cần admin role)
```powershell
pnpm dev
```
Mở browser với admin user:
- `/admin/api-keys` → table group by provider + form Add Key.
- Click "Add Key" → form provider/label/value/budget → submit → row mới xuất hiện.
- Click "Test" → spinner → kết quả `ok: true, latency_ms: <int>`.
- Click "Rotate" → prompt new value → submit → row cũ archive, row mới active.
- `/admin/alerts` → empty state "No alerts 🎉" (nếu chưa trigger budget).

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 14 MSEW step phải PASS verify command của riêng nó, VÀ 10 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase7-admin-api-keys.md` và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Sprint A4)
- **Worker refactor** — refactor `apps/worker/services/*.py` để dùng `key_resolver.resolve_key()` thay vì `os.environ`.
- **Service Routing Config** (`/api/admin/routing-config`) — CRUD 8 features.
- **Redis pub/sub** — invalidate `key_resolver` cache ngay khi admin rotate.
- **Cost tracking cron** — reset `current_month_cost_usd` đầu tháng.
- **2FA bắt buộc cho super_admin** — Phase 9.
- **Audit log viewer UI** (`/admin/audit-logs`) — Phase 9.