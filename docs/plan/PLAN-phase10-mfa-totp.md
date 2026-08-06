# Kế hoạch Triển khai (PLAN): phase10-mfa-totp

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Post-MVP Extension #1 — MFA TOTP cho super_admin. Phase bảo mật quan trọng nhất, đóng critical security gap khi super_admin có full quyền xóa user + rotate key + export audit log.
- **Giá trị cốt lõi:**
  1. Super admin PHẢI có TOTP (RFC 6238) cho critical operations (delete user, rotate API key, export audit log).
  2. Backup codes (10 codes) cho recovery khi mất authenticator.
  3. UI setup wizard 3 step: scan QR → verify code → save backup codes.
  4. Audit log mọi MFA event (enroll, verify, disable).

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: TOTP (pyotp) + Backup codes + JWT amr claim
```
[Super admin setup MFA]
  → POST /api/admin/mfa/enroll
    → Generate secret (pyotp.random_base32)
    → Generate QR code (qrcode library)
    → Store secret encrypted in mfa_challenges (status=pending)
    → Return {secret, qr_uri, backup_codes [10 codes, hashed]}

[Super admin verify code]
  → POST /api/admin/mfa/verify {code: "123456"}
    → pyotp.TOTP(secret).verify(code, valid_window=1)
    → If valid → status=active, return success
    → If invalid → return 401

[Critical operation (delete user / rotate key / export audit)]
  → Frontend includes X-MFA-Code header (TOTP code)
  → Backend dependency check: if super_admin + action critical → require X-MFA-Code
    → Verify via pyotp.TOTP
    → If invalid → 401 MFA_REQUIRED
```

### Cấu trúc file
```
supabase/migrations/
  0027_mfa_challenges.sql                (NEW) - 2 tables + RLS

apps/api/services/
  mfa.py                                (NEW) - TOTP verify + backup code verify
  mfa_setup.py                          (NEW) - enrollment flow

apps/api/dependencies/
  admin.py                              (UPDATE) - require_super_admin_with_mfa

apps/api/routers/
  admin_mfa.py                          (NEW) - 5 endpoints
  admin_users.py                        (UPDATE) - DELETE check MFA
  admin_api_keys.py                     (UPDATE) - DELETE/rotate check MFA
  admin_audit.py                        (UPDATE) - export CSV check MFA

apps/api/main.py                        (UPDATE) - mount admin_mfa router

apps/web/app/api/admin/mfa/
  route.ts                              (NEW) - GET status + POST enroll
  verify/route.ts                       (NEW) - POST verify code
  disable/route.ts                      (NEW) - POST disable

apps/web/app/(admin)/admin/security/mfa/
  page.tsx                              (NEW) - 3-step setup wizard

apps/web/app/(admin)/layout.tsx         (UPDATE) - add Security submenu
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Supabase MFA native (ĐÃ LOẠI một phần)
- **Lý do:** Supabase MFA chỉ work với email/SMS/phone, KHÔNG support custom TOTP QR code. Dùng `pyotp` cho custom flow + backup codes.

### Phương án B — SMS OTP (ĐÃ LOẢI)
- **Lý do:** Không secure (SIM swap attack). TOTP là chuẩn industry.

### Phương án C — Hardware key (FIDO2/WebAuthn) (ĐÃ LOẢI)
- **Lý do:** UX kém cho team nhỏ. Phase 10 dùng TOTP app (Google Authenticator / 1Password).

### Phương án D — Bắt buộc MFA cho admin role (ĐÃ LOẢI)
- **Lý do:** Theo plan, chỉ `super_admin` mới cần MFA (admin có thể manage user thường). Phase 11+ mở rộng.

### Lý do chọn phương án hiện tại
- **TOTP chuẩn RFC 6238** — Google Authenticator / 1Password / Authy đều support.
- **Backup codes** — 10 codes dùng 1 lần, hash SHA-256.
- **Window tolerance ±1 (60s)** — balance UX vs security.
- **Middleware check header** — không phá vỡ user-facing flow.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Super admin mất authenticator + backup codes → lockout | **Cao** | 10 backup codes × 1 lần = 10 attempts. Recovery qua DB manual reset (doc cho on-call). |
| 2 | TOTP secret leak trong DB → attacker bypass MFA | Trung bình | Encrypt secret bằng `apps/api/services/vault.py` (Fernet, Phase 7 đã có). |
| 3 | Timing attack compare backup code | Thấp | `hmac.compare_digest()` constant-time compare. |
| 4 | Window tolerance ±1 → replay attack trong 30s | Thấp | Phase 10 strict ±1. Phase 11+ thêm nonce. |
| 5 | UI prompt MFA mỗi lần critical op → UX kém | Trung bình | Cache `mfa_verified` 5 phút trong session (không phải mỗi request). |
| 6 | Backup code dùng nhiều lần → fail rate cao | Thấp | Phase 10 strict 1 lần. Phase 11+ cho phép 2 lần. |
| 7 | Migration fail vì RLS policy conflict | Thấp | Default deny (no explicit policy), service_role bypass. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~900 lines (50 SQL + 300 Python services + 200 Python router + 250 TypeScript + 100 markdown) |
| **Timeline** | 11 steps MSEW, ước tính 5-7 giờ Tier 2 thực thi + verify |
| **Files touched** | 7 NEW + 5 UPDATE (1 migration + 2 services + 1 router + 3 proxy + 1 UI + 1 sidebar + 3 admin routers + 1 main.py + 1 admin.py) |

## 6. Phụ thuộc giữa các Step
- Step 1 (migration) → trigger tạo ngay.
- Step 2 (mfa.py) → Step 3 (mfa_setup.py) dùng.
- Step 2-3 (services) → Step 4 (admin.py) dùng.
- Step 5 (3 router update) → Step 6 (admin_mfa) integration.
- Step 6 (router) → Step 7 (main.py mount).
- Step 8 (web proxy) → Step 9 (UI page).
- Step 10 (sidebar) sau Step 9.
- Step 11 (verify) cuối cùng.