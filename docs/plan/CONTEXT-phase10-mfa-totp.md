# Bối cảnh Hệ thống (CONTEXT): phase10-mfa-totp

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A5 extension)
- **Admin Panel MVP đã xong (Phase 5-9):** 13 features, 32 endpoint, 7 UI page.
- **Đây là Phase 10 — Post-MVP Extension #1:** MFA TOTP cho super_admin.

## 2. Codebase Analysis (qua Read + Grep)

### Discovery — Auth chain hiện tại
- **`apps/api/dependencies/auth.py:14`** — `get_supabase_user()` verify JWT, return `user_id`.
- **`apps/api/dependencies/admin.py:15`** — `require_admin(user_id)` check role ∈ {'admin', 'super_admin'}, cache 60s.
- **`apps/api/services/credit_manager.py`** — `get_user_role(user_id)` query DB.
- **Mọi router admin Phase 5/6/7/8/9** dùng `Depends(require_admin)`.

### Supabase MFA support
- Supabase Auth hỗ trợ MFA TOTP từ 2024+ (multi-factor authentication với authenticator app).
- Pattern: user enroll TOTP qua `supabase.auth.mfa.enroll()` → scan QR code → verify code qua `supabase.auth.mfa.verify()`.
- JWT chứa `amr` claim (authentication methods reference) — `["password", "totp"]` nếu cả 2 đều dùng.
- **Phase 10 sẽ check JWT claim `amr` có chứa `"totp"` không** cho super_admin.

### Hiện trạng cần thêm (qua Grep)
- ❌ **KHÔNG CÓ** `apps/api/services/mfa.py` (TOTP verify helper).
- ❌ **KHÔNG CÓ** `apps/api/services/mfa_setup.py` (enrollment flow).
- ❌ **KHÔNG CÓ** `mfa_challenges` table trong DB (track challenge state).
- ❌ **KHÔNG CÓ** `apps/api/routers/admin_mfa.py` (MFA setup + verify endpoints).
- ❌ **KHÔNG CÓ** UI trang `/admin/security/mfa`.

### Files KHÔNG tồn tại (cần tạo mới)
- `supabase/migrations/0027_mfa_challenges.sql` — challenge tracking.
- `apps/api/services/mfa.py` — TOTP verify + window tolerance.
- `apps/api/services/mfa_setup.py` — enrollment flow (generate secret, store, verify code).
- `apps/api/dependencies/admin.py` (UPDATE) — `require_super_admin_with_mfa` thay cho `require_admin` (cho super_admin only).
- `apps/api/routers/admin_mfa.py` — 5 endpoints (status, enroll, verify, disable, regenerate-backup-codes).
- `apps/web/app/api/admin/mfa/route.ts` — web proxy.
- `apps/web/app/api/admin/mfa/verify/route.ts` — web proxy.
- `apps/web/app/(admin)/admin/security/mfa/page.tsx` — UI setup wizard.

### Files cần UPDATE (minimal)
- `apps/api/routers/admin_users.py` (Phase 6) — DELETE/ban operations thêm MFA header check.
- `apps/api/routers/admin_api_keys.py` (Phase 7) — DELETE/rotate thêm MFA header check.
- `apps/api/routers/admin_audit.py` (Phase 9) — Export CSV thêm MFA header check.
- `apps/web/app/(admin)/layout.tsx` — Thêm submenu "Security" > MFA.

## 3. Các File liên quan và Vai trò

### Migration (1 NEW)
- `supabase/migrations/0027_mfa_challenges.sql` — `mfa_challenges` table + `mfa_backup_codes` table.

### Backend services (2 NEW)
- `apps/api/services/mfa.py` — TOTP verify (RFC 6238) + window tolerance.
- `apps/api/services/mfa_setup.py` — Enrollment flow (generate secret + QR + verify).

### Backend dependency (1 UPDATE)
- `apps/api/dependencies/admin.py` — Thêm `require_super_admin_with_mfa` (strict).

### Backend routers (1 NEW)
- `apps/api/routers/admin_mfa.py` — 5 endpoints (status, enroll, verify, disable, regenerate-backup-codes).

### Frontend (2 NEW + 1 UPDATE)
- 2 web proxy routes.
- 1 UI setup wizard page.
- Sidebar thêm submenu Security.

## 4. Dependencies
- **External:** `pyotp` (Python TOTP library) — cần cài (`pip install pyotp`). `qrcode[pil]` cho QR generation (`pip install qrcode[pil]`).
- **Internal:** `apps.api.dependencies.admin.require_admin`, `apps.api.services.audit.log_admin_action`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **MFA chỉ bắt buộc cho `super_admin`**, KHÔNG bắt buộc `admin` (theo admin_panel_plan.md mục 2.7).
- **Backup codes:** 10 codes, mỗi code 8 ký tự alphanumeric. Lưu hashed (sha256) trong DB.
- **TOTP window:** 30s timestep, ±1 window tolerance (60s total).
- **Backward compatible:** Admin role hiện tại KHÔNG bị ảnh hưởng. Chỉ super_admin mới cần MFA.
- **Graceful degradation:** Nếu user chưa enroll MFA → middleware allow request (warning log), nhưng mark `mfa_required` để UI prompt setup.
- **Audit log:** Mọi MFA event (enroll, verify, disable) phải ghi audit.

## 6. Output mong đợi

Sau Phase 10:
- Super admin lần đầu vào `/admin/security/mfa` → thấy banner "MFA chưa setup".
- Click "Setup MFA" → QR code + secret key hiển thị.
- Scan QR bằng Google Authenticator / 1Password → nhập 6-digit code → verify thành công.
- Lưu 10 backup codes → confirm → MFA active.
- Lần sau super_admin thực hiện critical operation (delete user, rotate key, export audit log) → frontend yêu cầu nhập TOTP code → backend verify `amr` claim.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- Migration 0027 apply thành công (2 tables: mfa_challenges + mfa_backup_codes).
- 2 service mới (`mfa.py`, `mfa_setup.py`).
- 1 dependency update (`require_super_admin_with_mfa`).
- 5 endpoint MFA setup flow.
- 2 web proxy + 1 UI setup wizard + sidebar update.
- TS compile 0 errors.
- Existing pytest PASSED.
- Test enrollment: generate secret → verify code qua pyotp → success.
- Test invalid code: reject.
- Test backup code: 1 backup code dùng 1 lần, hash stored.
- Test window tolerance: code từ ±30s vẫn accept.