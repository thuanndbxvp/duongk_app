# Bối cảnh Hệ thống (CONTEXT): phase6-admin-user-credit

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A2)
- **Phase 5 đã viết xong** (CONTEXT-phase5-audit-fixes-foundation.md): `require_admin` + `audit.py:log_admin_action` + migration 0022 (role, audit_logs, RPCs) + AdminShell + Dashboard `/admin` (stub).
- **Đây là Sprint A2:** User & Credit Management. Cần theo checklist admin_panel_plan.md mục 2.7:
  - 8 endpoint `/api/admin/users` (GET, POST, PATCH, DELETE, restore, ban, unban, impersonate) + `/api/admin/users/{id}` (GET) + `/api/admin/users/{id}/adjust-credit` (POST).
  - 4 endpoint `/api/admin/credit/*` (ledger, stats, export, pricing).
  - UI: `/admin/users` + `/admin/users/[id]` + `/admin/credits`.
  - Soft-delete cron (Phase 7+).
  - Sidebar update: enable Users + Credits.

## 2. Codebase Analysis (qua Read trực tiếp)

### Discovery — Phase 5 đã chuẩn bị
- **`apps/api/dependencies/admin.py:15`** — `require_admin` dependency (cached 60s, return 403 nếu không phải admin/super_admin).
- **`apps/api/services/audit.py:27`** — `log_admin_action()` với `_mask_value()` (regex `(key|token|secret|password|api_key)`).
- **`supabase/migrations/0022_admin_panel_foundation.sql`** — đã có:
  - `users` columns: `role`, `max_assistants`, `banned_at`, `banned_reason`, `deleted_at`, `last_sign_in_at`.
  - `admin_audit_logs` table (RLS deny non-service).
  - RPC `admin_adjust_credits(p_admin_id, p_user_id, p_delta, p_reason)` — atomic + audit.
  - RPC `soft_delete_user(p_user_id)` — soft delete.

### Related Symbols (qua Read + Grep)
- `users` table: columns `id, email, credits, tier, role, max_assistants, banned_at, banned_reason, deleted_at, last_sign_in_at, created_at, updated_at` (0022 + 0001).
- `credit_transactions` table: columns `id, user_id, job_id, action, amount, balance_after, reason, metadata, created_at` (0003 + 0022).
- `jobs` table: columns `id, user_id, task_type, status, credits_held, assistant_id, channel_id, created_at, updated_at`.
- `channel_assistants` table: columns `id, user_id, youtube_url, channel_id, status, ...`.
- `credit_pricing` table: columns `job_type, credits, description, enabled` (0020 + 0022 thêm `updated_by`, `updated_at`).

### Existing endpoints admin KHÔNG có
- **0 admin routes mounted** trong `apps/api/main.py` hiện tại.

### Existing web admin UI (Phase 5 đã có)
- `apps/web/app/(admin)/layout.tsx` — AdminShell sidebar (8 mục, Users + Credits + Pricing + others disabled với "Soon" badge).
- `apps/web/app/(admin)/admin/page.tsx` — Dashboard 4 stat cards với data "—" placeholder.
- **CHƯA CÓ** trang `/admin/users`, `/admin/users/[id]`, `/admin/credits`.

### Callers Analysis (qua Read layout.tsx)
- Layout check role: `if (!['admin', 'super_admin'].includes(role)) redirect('/403');` — OK.
- Layout sidebar: ADMIN_NAV array, mỗi item có `enabled: bool`. Phase 6 cần đổi `Users.enabled = true`, `Credits.enabled = true`.

### Callees Analysis (Phase 6 mới)
- Admin endpoints mới sẽ gọi:
  - `require_admin` (đã có).
  - `get_supabase_admin()` (đã có).
  - `log_admin_action()` (đã có).
  - RPC `admin_adjust_credits` (đã có ở 0022).
  - RPC `soft_delete_user` (đã có ở 0022).

## 3. Các File liên quan và Vai trò

### Backend (apps/api) - CẦN TẠO MỚI
| File | Mount | Routes |
|------|-------|--------|
| `apps/api/routers/admin_users.py` (NEW) | `/api/admin/users` | GET list, GET one, POST create, PATCH update, DELETE, POST restore, POST ban, POST unban, POST impersonate, POST adjust-credit |
| `apps/api/routers/admin_credit.py` (NEW) | `/api/admin/credit` | GET ledger, GET stats, GET export, GET pricing |
| `apps/api/routers/admin_pricing.py` (NEW) | `/api/admin/pricing` | PATCH (per job_type), POST reload |

### Backend (apps/api) - UPDATE
| File | Update |
|------|--------|
| `apps/api/main.py` | Mount 3 routers admin mới |
| `apps/api/routers/credits.py` | KHÔNG đụng (user-facing `/credits/balance`) |

### Frontend (apps/web) - CẦN TẠO MỚI
| File | Vai trò |
|------|---------|
| `apps/web/app/(admin)/admin/users/page.tsx` (NEW) | Table user với filter, search, pagination |
| `apps/web/app/(admin)/admin/users/[id]/page.tsx` (NEW) | User detail với tabs Profile/Credits/Jobs + action bar |
| `apps/web/app/(admin)/admin/credits/page.tsx` (NEW) | Ledger table + 4 stat cards + Export CSV button |

### Frontend - Web proxy mới
| File | Vai trò |
|------|---------|
| `apps/web/app/api/admin/users/route.ts` (NEW) | GET list + POST create |
| `apps/web/app/api/admin/users/[id]/route.ts` (NEW) | GET one + PATCH |
| `apps/web/app/api/admin/users/[id]/adjust-credit/route.ts` (NEW) | POST adjust |
| `apps/web/app/api/admin/credits/ledger/route.ts` (NEW) | GET ledger |

### Frontend - UPDATE
| File | Update |
|------|--------|
| `apps/web/app/(admin)/layout.tsx` | Đổi `Users.enabled = true`, `Credits.enabled = true` (line 9, 10) |

### Files KHÔNG đụng
- `apps/api/dependencies/admin.py` (require_admin - Phase 5 đã viết).
- `apps/api/services/audit.py` (Phase 5 đã viết).
- `supabase/migrations/0022_admin_panel_foundation.sql` (Phase 5 đã apply).
- `apps/api/routers/{projects,users,credits}.py` (user-facing routes).
- `apps/api/services/credit_manager.py`.
- Tất cả worker tasks (Phase 1-5 không đụng).

## 4. Dependencies
- **External:** fastapi, pydantic, supabase-py, csv (stdlib). Đã có hết.
- **Internal:** `apps.api.dependencies.admin.require_admin`, `apps.api.dependencies.auth.get_supabase_user`, `apps.api.dependencies.supabase.get_supabase_admin`, `apps.api.services.audit.log_admin_action`, `apps.api.services.credit_manager.CreditManager`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Không thêm dependency mới.**
- **Tất cả endpoint admin** PHẢI có `Depends(require_admin)` (Phase 5 đã có sẵn).
- **Audit mask:** Tất cả mutation phải gọi `log_admin_action()` để ghi log + tự mask.
- **Không đụng Phase 5 files:** `require_admin`, `audit.py`, migration 0022.
- **Không đụng user-facing routes:** `/api/users/*`, `/api/credits/*` (user), `/api/assistants/*`, `/api/jobs/*`, `/api/channels/collect`.
- **Impersonate:** Phase 6 chỉ viết **stub** (return mock token) — full JWT signing Phase 7+.
- **Soft-delete cron:** Phase 6 chỉ viết RPC `soft_delete_user` (đã có ở 0022) — cron job thật Phase 7+.

## 6. Output mong đợi

Sau Phase 6:
- Admin user click `/admin/users` → thấy table user với data thật.
- Click row → `/admin/users/[id]` → thấy profile + credits + jobs + tabs.
- Click "Adjust Credit" → form delta + reason → RPC `admin_adjust_credits` → audit log ghi.
- Click `/admin/credits` → thấy ledger + 4 stat cards + Export CSV.
- Mọi mutation đều có entry trong `admin_audit_logs` (xem qua Supabase Dashboard).

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- 13 endpoint admin mới + mount vào `main.py`.
- 3 trang admin mới + 4 web proxy routes + sidebar update.
- Verify: `/admin/users` load được user list (qua mock JWT), `/admin/credits` load được ledger.
- Audit log ghi được (test với mock admin).
- 0 regression trên user-facing routes.