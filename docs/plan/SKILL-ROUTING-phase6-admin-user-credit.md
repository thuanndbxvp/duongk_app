# Phân bổ Kỹ năng (SKILL-ROUTING): phase6-admin-user-credit

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 6 là **Sprint A2** trong admin_panel_plan.md. Phạm vi lớn nhất trong tất cả phase:
- **Backend:** 13 endpoint admin (users CRUD + credit ledger + pricing) + mount.
- **Frontend:** 3 trang admin + 4 web proxy + sidebar update.
- **Audit:** 100% mutation có `log_admin_action()`.

Skill chính: `backend-development` (FastAPI CRUD + Supabase) + `frontend-development` (Next.js admin UI) + `better-auth` (RBAC pattern) + `devops` (IP whitelist check).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Tạo `apps/api/routers/admin_users.py` (9 endpoints) | `backend-development` | `better-auth` | `database-admin` | CRUD + RBAC + audit |
| Step 2 | Tạo `apps/api/routers/admin_credit.py` (4 endpoints) | `backend-development` | `database-admin` | `debugging` | Query ledger + export CSV |
| Step 3 | Tạo `apps/api/routers/admin_pricing.py` (2 endpoints) | `backend-development` | `database-admin` | `debugging` | PATCH + reload |
| Step 4 | UPDATE `apps/api/main.py` mount 3 routers admin | `backend-development` | `debugging` | `code-review` | Integration step |
| Step 5 | Tạo `apps/web/app/api/admin/users/route.ts` | `frontend-development` | `better-auth` | `debugging` | Next.js proxy admin |
| Step 6 | Tạo 3 web proxy routes còn lại (user detail, adjust-credit, credits/ledger) | `frontend-development` | `better-auth` | `debugging` | Next.js proxy admin |
| Step 7 | Tạo `apps/web/app/(admin)/admin/users/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | Admin user table |
| Step 8 | Tạo `apps/web/app/(admin)/admin/users/[id]/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | User detail tabs |
| Step 9 | Tạo `apps/web/app/(admin)/admin/credits/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | Ledger + stats |
| Step 10 | UPDATE `apps/web/app/(admin)/layout.tsx` enable Users + Credits | `frontend-development` | `ui-styling` | `debugging` | Sidebar update |
| Step 11 | Self-verify toàn bộ (imports + TS compile + manual UI check) | `debugging` | `code-review` | `backend-development` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `better-auth`: RBAC enforcement — mọi endpoint admin phải `Depends(require_admin)`.
- `database-admin`: SQL queries phức tạp (filter + paginate + group by) cho ledger.
- `ui-styling`: Admin UI dùng glass system + token variables.
- `code-review`: Scan security — verify ownership, IP whitelist (mock trong dev), audit log không leak secret.
- `debugging`: Nếu import fail hoặc TS compile error.

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** sửa `apps/api/dependencies/admin.py` (require_admin đã đúng).
- ❌ **CẤM** sửa `apps/api/services/audit.py` (audit log đã có mask).
- ❌ **CẤM** sửa migration `0022` (Phase 5 đã apply).
- ❌ **CẤM** đụng user-facing routes (`/api/users/*`, `/api/credits/*`, `/api/assistants/*`, `/api/jobs/*`, `/api/channels/collect`).
- ❌ **CẤM** đụng `apps/api/services/credit_manager.py` (Phase 5 đã có `get_user_role`).
- ❌ **CẤM** tạo endpoint admin KHÔNG có `Depends(require_admin)`.
- ❌ **CẤM** mutation admin mà KHÔNG gọi `log_admin_action()`.
- ❌ **CẤM** commit secret thật.
- ❌ **CẦM** full implement impersonate JWT (Phase 6 chỉ stub).
- ❌ **CẤM** soft-delete cron (Phase 7+).