# Tiêu chí Nghiệm thu (ACCEPTANCE): phase10-mfa-totp

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `supabase/migrations/0027_mfa_challenges.sql` (NEW)
- [ ] Có bảng `mfa_challenges` với columns: `id`, `user_id`, `status` (pending/active/disabled), `encrypted_secret BYTEA`, `qr_uri`, `enrolled_at`, `last_verified_at`, `failed_attempts`, `locked_until`.
- [ ] Có UNIQUE constraint `(user_id, status)` (deferrable).
- [ ] Có bảng `mfa_backup_codes` với columns: `id`, `user_id`, `code_hash`, `used_at`.
- [ ] Có index `idx_mfa_user_status` + `idx_backup_codes_user`.
- [ ] Có RPC `record_mfa_failure(p_user_id)` (atomic increment + auto-lock).
- [ ] RLS enabled trên cả 2 tables.

### File 2: `apps/api/services/mfa.py` (NEW)
- [ ] Có hàm `generate_secret() → str` (pyotp.random_base32).
- [ ] Có hàm `verify_totp(secret, code, valid_window=1) → bool` (window ±1).
- [ ] Có hàm `generate_backup_codes(count=10, length=8) → list[str]` (no 0/1/I/O confusion).
- [ ] Có hàm `hash_backup_code(code) → str` (SHA-256 hex).
- [ ] Có hàm `verify_backup_code(user_id, code) → bool` (atomic mark used).
- [ ] Có hàm `is_user_locked(user_id) → bool` (check `locked_until` > NOW).
- [ ] Có hàm `record_failed_attempt(user_id) → int` + `reset_failed_attempts(user_id)`.

### File 3: `apps/api/services/mfa_setup.py` (NEW)
- [ ] Có hàm `start_enrollment(user_id, user_email) → dict` (return `{secret, qr_uri, qr_png_base64, backup_codes}`).
- [ ] QR code base64 PNG generated.
- [ ] Secret encrypt bằng `vault.encrypt()` (Phase 7).
- [ ] Có hàm `verify_and_activate(user_id, code) → bool` (verify → status=active).
- [ ] Có hàm `get_active_secret(user_id) → str` (cho header check).
- [ ] Có hàm `disable_mfa(user_id) → bool`.

### File 4: `apps/api/dependencies/admin.py` (UPDATE)
- [ ] Có function `require_super_admin(user_id) → str` (role=super_admin only).
- [ ] Có function `require_mfa_for_critical(user_id, mfa_code) → bool`.
- [ ] Non-super_admin bypass (return True).
- [ ] Super_admin + missing code → 401.
- [ ] Super_admin + invalid code → 401 (tăng failed_attempts).
- [ ] Super_admin + 5 failed → 423 (locked 15 min).
- [ ] KHÔNG sửa `require_admin()` (giữ backward compat).

### File 5-7: 3 router UPDATE
- [ ] `admin_users.py` DELETE endpoint check `X-MFA-Code` header.
- [ ] `admin_api_keys.py` DELETE + rotate endpoint check `X-MFA-Code` header.
- [ ] `admin_audit.py` export CSV endpoint check `X-MFA-Code` header.
- [ ] Tất cả check qua `require_mfa_for_critical()`.

### File 8: `apps/api/routers/admin_mfa.py` (NEW)
- [ ] Có 5 endpoints:
  - `GET /api/admin/mfa` (status: not_enrolled/pending/active/disabled)
  - `POST /api/admin/mfa/enroll` (start enrollment → return secret + QR + backup_codes)
  - `POST /api/admin/mfa/verify` (verify 6-digit → activate)
  - `POST /api/admin/mfa/disable` (require verify → disable)
  - `POST /api/admin/mfa/regenerate-backup-codes` (verify → new 10 codes, invalidate old)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Mọi mutation gọi `log_admin_action()`.

### File 9: `apps/api/main.py` (UPDATE)
- [ ] Có import mới: `admin_mfa_router`.
- [ ] Có `app.include_router(admin_mfa_router)`.
- [ ] Admin MFA route count ≥ 6.

### File 10-13: Web proxy routes (4 NEW)
- [ ] `apps/web/app/api/admin/mfa/route.ts` (GET).
- [ ] `apps/web/app/api/admin/mfa/verify/route.ts` (POST).
- [ ] `apps/web/app/api/admin/mfa/disable/route.ts` (POST).
- [ ] `apps/web/app/api/admin/mfa/regenerate-backup-codes/route.ts` (POST).
- [ ] TS compile 0 errors.

### File 14: `apps/web/app/(admin)/admin/security/mfa/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] 3-step wizard: Step 1 (Setup) → Step 2 (Scan QR + verify) → Step 3 (Save backup codes).
- [ ] QR code hiển thị base64 PNG inline.
- [ ] Backup codes hiển thị grid 2 cols + Copy all button.
- [ ] Disable MFA có input code trước khi submit.

### File 15: `apps/web/app/(admin)/layout.tsx` (UPDATE)
- [ ] Thêm dòng `Security` enabled=true sau Audit Logs.
- [ ] 8 mục còn lại KHÔNG đổi.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Security:**
  - TOTP secret ENCRYPT bằng Fernet (Phase 7 `vault.encrypt()`).
  - Backup codes HASH SHA-256 trước khi lưu DB.
  - Constant-time compare qua `pyotp` (timing-safe).
  - 5 failed attempts → lockout 15 phút.
  - Window tolerance ±1 (60s total).
  - Audit log mọi MFA event.
- **Backward compatibility:**
  - Non-super_admin KHÔNG bị ảnh hưởng (bypass MFA check).
  - 32 admin endpoints Phase 5-9 vẫn hoạt động bình thường (require_admin vẫn cho phép admin role).
- **UX:**
  - 3-step wizard intuitive.
  - QR code visible ngay.
  - Backup codes dạng grid dễ save.
  - Disable flow an toàn (yêu cầu verify trước).
- **No new dependency conflict:**
  - `pyotp` (RFC 6238) — pip install.
  - `qrcode[pil]` — pip install.
- **Recovery:**
  - 10 backup codes × 1 lần = 10 recovery attempts.
  - Manual DB reset cho on-call (Phase 10 doc).

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 10 KHÔNG thêm unit test mới. Verify qua smoke test:
  - pyotp roundtrip (generate → verify same code).
  - Backup code generation + hash consistency.
  - Window tolerance (verify ±1).
- **Frontend:** TS compile 0 errors.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify pip packages installed
```powershell
pip show pyotp
pip show qrcode
```
**Expected:** 2 packages with version.

### Bước 2: Verify Python imports (5 file)
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.mfa import generate_secret, verify_totp, generate_backup_codes; print('mfa OK')"
python -c "from apps.api.services.mfa_setup import start_enrollment, verify_and_activate; print('mfa_setup OK')"
python -c "from apps.api.dependencies.admin import require_admin, require_super_admin, require_mfa_for_critical; print('admin deps OK')"
python -c "from apps.api.routers.admin_mfa import router; print('admin_mfa OK')"
```
**Expected:** 5 dòng "OK".

### Bước 3: Verify TOTP roundtrip
```powershell
python -c "from apps.api.services.mfa import generate_secret, verify_totp; import pyotp; s = generate_secret(); c = pyotp.TOTP(s).now(); assert verify_totp(s, c) == True; print('roundtrip OK')"
```
**Expected:** `roundtrip OK`.

### Bước 4: Verify backup code generation
```powershell
python -c "from apps.api.services.mfa import generate_backup_codes, hash_backup_code; cs = generate_backup_codes(count=10); print('codes:', cs[:3]); print('len:', len(cs)); assert hash_backup_code(cs[0]) == hash_backup_code(cs[0]); print('hash consistent OK')"
```
**Expected:** 10 codes + hash consistent.

### Bước 5: Verify admin MFA routes count
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'mfa' in r.path]); print(len(routes), 'mfa routes'); [print(r) for r in routes]"
```
**Expected:** ≥ 6 routes.

### Bước 6: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 7: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 8: Verify UI page + sidebar
```powershell
Test-Path "app\(admin)\admin\security\mfa\page.tsx"
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "Security.*enabled.*true"
```
**Expected:** 1 page + 1 sidebar match.

### Bước 9: MFA header check test (manual)
```powershell
# Start dev server
cd d:\appDK
uvicorn apps.api.main:app --reload

# Test 1: admin role DELETE user KHÔNG cần MFA
curl -X DELETE http://localhost:8000/api/admin/users/<user_id> \
  -H "Authorization: Bearer <admin-token>"
# Expected: 200 OK (admin role bypass MFA)

# Test 2: super_admin role DELETE user KHÔNG có X-MFA-Code → 401
curl -X DELETE http://localhost:8000/api/admin/users/<user_id> \
  -H "Authorization: Bearer <super-admin-token>"
# Expected: 401 MFA_REQUIRED

# Test 3: super_admin DELETE user + valid TOTP code → 200
curl -X DELETE http://localhost:8000/api/admin/users/<user_id> \
  -H "Authorization: Bearer <super-admin-token>" \
  -H "X-MFA-Code: 123456"
# Expected: 200 OK (or whatever current TOTP code is)
```

### Bước 10: Visual smoke test (optional, cần super_admin role)
```powershell
pnpm dev
```
Mở browser với super_admin user:
- `/admin/security/mfa` → status "Not enrolled".
- Click "Generate QR Code" → Step 2 hiển thị QR.
- Scan QR bằng Google Authenticator / 1Password.
- Nhập 6-digit code → click Verify → Step 3 hiển thị 10 backup codes.
- Copy backup codes → click Done.
- Reload page → status "Active".
- Vào `/admin/users` → click Delete → prompt TOTP code → nhập → confirm.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 11 MSEW step phải PASS verify command của riêng nó, VÀ 10 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase10-mfa-totp.md` và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Phase 11+)
- **MFA cho admin role** (currently bypass — Phase 11+ mở rộng).
- **WebAuthn / FIDO2** (Phase 12+).
- **Session-based MFA cache** (5 phút session thay vì mỗi request).
- **MFA recovery flow** (admin có thể reset MFA của super_admin khác qua audit + manual approval).
- **MFA enrollment audit log** (currently Phase 10 có `mfa.enroll_started` + `mfa.activated` — Phase 11+ có thêm chi tiết).
- **Advanced dashboard analytics** (cohort retention, revenue chart).
- **Backup cron** (Phase 12).