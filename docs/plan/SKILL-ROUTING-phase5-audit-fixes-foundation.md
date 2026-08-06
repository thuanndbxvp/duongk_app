# Phân bổ Kỹ năng (SKILL-ROUTING): phase5-audit-fixes-foundation

## 1. Chiến lược tổng thể (Overall Strategy)
Phase này tập trung 3 trụ cột:
1. **Database cleanup** (skill `databases`): migration 0022 dọn duplicate `hold_credits`, fix RLS transcripts, thêm columns cho admin.
2. **Backend RBAC scaffold** (skill `backend-development` + `better-auth`): dependency `require_admin`, audit log service.
3. **Frontend admin shell** (skill `frontend-development` + `web-frameworks`): Next.js middleware + layout admin.

Không đụng AI/ML logic (TTS, embed, RAG) — những phần đó để các phase sau.

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Drop duplicate `hold_credits` (0006) | `databases` | `backend-development` | `debugging` | Sửa SQL migration order |
| Step 2 | Fix RLS `transcripts` (0011) | `databases` | `better-auth` | `debugging` | RLS security fix |
| Step 3 | Migration `0022_admin_panel_foundation.sql` (role/max_assistants/banned_at/deleted_at + admin_audit_logs table) | `databases` | `backend-development` | `planning` | Thêm columns + table mới |
| Step 4 | RPC `admin_adjust_credits` + `soft_delete_user` | `databases` | `backend-development` | `debugging` | SQL function cho admin ops |
| Step 5 | Update `credit_manager.py` để export `get_user_role()` (helper) | `backend-development` | `better-auth` | `databases` | Python helper |
| Step 6 | Tạo `apps/api/dependencies/admin.py:require_admin` | `better-auth` | `backend-development` | `debugging` | RBAC dependency |
| Step 7 | Tạo `apps/api/services/audit.py:log_admin_action` với mask helper | `backend-development` | `better-auth` | `code-review` | Audit service |
| Step 8 | Tạo `apps/web/middleware.ts` check role cho `/admin/**` | `frontend-development` | `web-frameworks` | `better-auth` | Next.js middleware |
| Step 9 | Tạo route group `apps/web/app/(admin)/layout.tsx` (AdminShell) | `frontend-development` | `ui-styling` | `aesthetic` | Layout shell |
| Step 10 | Tạo trang `/admin` placeholder với 4 stat cards | `frontend-development` | `ui-styling` | `aesthetic` | Dashboard placeholder |
| Step 11 | Update `apps/api/main.py` để mount audit router placeholder (nếu có) hoặc verify không regression | `backend-development` | `debugging` | `code-review` | Integration check |
| Step 12 | Self-verify: chạy unit test + smoke test API | `debugging` | `code-review` | `backend-development` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `debugging`: Khi bất kỳ verify command nào fail.
- `code-review`: Sau khi code xong mỗi step, scan security + scope creep.
- `codegraph_impact`: Sau step 6-7, check xem `require_admin` dependency có ảnh hưởng đến router nào đang chạy production không (expect: 0 vì chưa có router admin).

## 4. Cấm kỵ (Forbidden)
- ❌ **CẤM** tự ý thêm column vào bảng `users` ngoài 6 column đã liệt kê trong CONTEXT.
- ❌ **CẤM** đụng `apps/api/routers/projects.py` (đang chạy production).
- ❌ **CẤM** đụng `apps/api/modules/voice/*` (TTS đang hoạt động).
- ❌ **CẤM** cài dependency mới (`pnpm add`, `pip install`).
- ❌ **CẤM** xoá hoặc sửa file trong `supabase/migrations/` từ 0001 đến 0021.
