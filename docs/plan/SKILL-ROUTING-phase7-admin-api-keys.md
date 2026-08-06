# Phân bổ Kỹ năng (SKILL-ROUTING): phase7-admin-api-keys

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 7 là **Sprint A3** trong admin_panel_plan.md. Phạm vi:
- **Backend:** 3 migration (api_provider_keys + api_usage_logs + admin_alerts) + 2 service (vault + key_resolver) + 2 router admin (9 endpoints).
- **Frontend:** 5 web proxy + 2 trang admin + sidebar update.
- **Encryption:** AES-GCM (Fernet) thay vì Supabase Vault — đơn giản hơn, không cần extension.

Skill chính: `backend-development` (security + encryption) + `database-admin` (schema design) + `frontend-development` (admin UI) + `devops` (env management).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Tạo migration `0023_api_provider_keys.sql` | `database-admin` | `backend-development` | `devops` | Schema + indexes |
| Step 2 | Tạo migration `0024_api_usage_logs.sql` | `database-admin` | `backend-development` | `debugging` | Cost tracking |
| Step 3 | Tạo migration `0025_admin_alerts.sql` | `database-admin` | `backend-development` | `debugging` | Alert schema |
| Step 4 | Tạo `apps/api/services/vault.py` | `backend-development` | `devops` | `debugging` | Fernet encryption |
| Step 5 | Tạo `apps/api/services/key_resolver.py` | `backend-development` | `database-admin` | `debugging` | Cache + fallback |
| Step 6 | Tạo `apps/api/services/usage_tracker.py` | `backend-development` | `database-admin` | `debugging` | Decorator pattern |
| Step 7 | Tạo `apps/api/routers/admin_api_keys.py` (7 endpoints) | `backend-development` | `better-auth` | `database-admin` | CRUD + test + rotate |
| Step 8 | Tạo `apps/api/routers/admin_alerts.py` (2 endpoints) | `backend-development` | `database-admin` | `debugging` | List + resolve |
| Step 9 | UPDATE `apps/api/main.py` mount 2 routers + import key_resolver | `backend-development` | `debugging` | `code-review` | Integration step |
| Step 10 | Tạo 5 web proxy routes | `frontend-development` | `better-auth` | `debugging` | Next.js proxy |
| Step 11 | Tạo `admin/api-keys/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | UI provider table |
| Step 12 | Tạo `admin/alerts/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | UI alerts list |
| Step 13 | UPDATE layout.tsx enable API Keys + Alerts | `frontend-development` | `ui-styling` | `debugging` | Sidebar update |
| Step 14 | Self-verify toàn bộ | `debugging` | `code-review` | `database-admin` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `database-admin`: Schema design + indexes + trigger.
- `backend-development`: Encryption + service pattern + RBAC.
- `frontend-development`: Admin UI consistent với Phase 6.
- `code-review`: Security audit — verify encryption + mask + role check.
- `debugging`: Nếu migration fail hoặc import error.

## 4. Cấm kỵ (Forbidden)
- ❌ **CẤM** sửa Phase 5 files (`require_admin`, `audit.py`, migration 0022).
- ❌ **CẤM** sửa Phase 6 files (chưa thực thi nhưng nếu Tier 2 đã viết thì KHÔNG đụng).
- ❌ **CẤM** đụng user-facing routes.
- ❌ **CẤM** đụng worker `os.environ` (giữ nguyên cho Phase 7).
- ❌ **CẤM** endpoint admin KHÔNG có `Depends(require_admin)`.
- ❌ **CẤM** mutation api-key KHÔNG gọi `log_admin_action()`.
- ❌ **CẤM** commit `ENCRYPTION_KEY` thật vào repo (chỉ placeholder + hướng dẫn generate).
- ❌ **CẤM** log raw key value ra console/Sentry/audit.
- ❌ **CẤM** refactor worker tasks Phase 7 (để Phase 8+).
- ❌ **CẤM** cron reset cost đầu tháng (Phase 9+).
- ❌ **CẤM** Supabase Vault (dùng Fernet AES-GCM).