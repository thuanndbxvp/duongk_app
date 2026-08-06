# Phân bổ Kỹ năng (SKILL-ROUTING): phase10-mfa-totp

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 10 là **Post-MVP Extension #1** — MFA TOTP cho super_admin. Phase bảo mật quan trọng nhất, mở rộng ngoài Admin Panel MVP (Phase 5-9).

Skill chính: `better-auth` (TOTP + Supabase MFA pattern) + `backend-development` (service + middleware) + `database-admin` (challenge tracking schema) + `frontend-development` (UI setup wizard).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Migration `0027_mfa_challenges.sql` | `database-admin` | `better-auth` | `backend-development` | Schema 2 tables + RLS |
| Step 2 | Service `mfa.py` (TOTP verify) | `better-auth` | `backend-development` | `debugging` | RFC 6238 implementation |
| Step 3 | Service `mfa_setup.py` (enrollment flow) | `better-auth` | `backend-development` | `debugging` | QR + secret generation |
| Step 4 | UPDATE `apps/api/dependencies/admin.py` | `better-auth` | `backend-development` | `code-review` | Add `require_super_admin_with_mfa` |
| Step 5 | UPDATE 3 router (header check) | `backend-development` | `better-auth` | `code-review` | Critical operation gating |
| Step 6 | Router `admin_mfa.py` (5 endpoints) | `better-auth` | `backend-development` | `database-admin` | MFA flow API |
| Step 7 | UPDATE `main.py` mount router | `backend-development` | `debugging` | `code-review` | Integration |
| Step 8 | 2 web proxy routes | `frontend-development` | `better-auth` | `debugging` | Next.js proxy |
| Step 9 | UI `admin/security/mfa/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | Setup wizard |
| Step 10 | UPDATE `layout.tsx` add submenu | `frontend-development` | `ui-styling` | `debugging` | Sidebar update |
| Step 11 | Self-verify toàn bộ | `debugging` | `code-review` | `better-auth` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `better-auth`: TOTP/QR pattern + Supabase MFA + backup codes.
- `backend-development`: Middleware + service pattern + dependency injection.
- `database-admin`: Schema design + RLS + hash storage.
- `code-review`: Security audit — verify timing-safe compare + bcrypt backup codes.
- `frontend-development`: UI setup wizard (3 step: scan → verify → save backup).

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** sửa Phase 5/6/7/8/9 files (ngoại trừ 3 router admin cần header check + layout.tsx sidebar).
- ❌ **CẤM** MFA bắt buộc cho `admin` role (chỉ `super_admin`).
- ❌ **CẤM** lưu backup code plaintext — PHẢI hash SHA-256.
- ❌ **CẤM** commit secret TOTP seed vào repo.
- ❌ **CẢM** disable MFA qua API không có MFA verification hiện tại.
- ❌ **CẤM** dùng time.time() không constant — phải dùng pyotp.compare_totp() (timing-safe).
- ❌ **CẤM** window tolerance > ±1 (60s total) — phase 10 strict, Phase 11+ mở rộng.
- ❌ **CẤM** endpoint MFA KHÔNG có `Depends(require_admin)` check trước (chỉ require admin, không yêu cầu super_admin để self-enroll).
- ❌ **CẤM** đụng user-facing routes.
- ❌ **CẤM** đụng JWT secret format (giữ nguyên `pyjwt` decode).