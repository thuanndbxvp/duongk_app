# Bối cảnh Hệ thống (CONTEXT): Phase 01 — Project foundation & Blank Project Onboarding

## 1. Tri thức Tổng hợp
- **Đường dẫn Repomix Bundle:** `.\CONTEXT_BUNDLE.md` (Tier 2 sẽ tự sinh bằng lệnh `repomix` trước khi code)
- **Phase plan gốc:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-01-project-foundation.md`
- **Master plan:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\plan.md`

## 2. Codebase Analysis (qua CodeGraph MCP — Tier 2 phải tự gọi trước khi sửa file)

### Discovery (từ `codegraph_explore`)
- Cụm `apps/web/app/(dashboard)/projects/` chứa UI tạo project hiện đang ép channel URL.
- Cụm `apps/api/routers/` có các router liên quan đến assistant và channel; cần kiểm tra trước khi mount router mới.
- Cụm `apps/worker/tasks/` có `script_generate.py`, `scene_breakdown.py`, `scene_breaker.py`.

### Related Symbols (từ `codegraph_search`)
- `ProjectCreatePage` at `apps/web/app/(dashboard)/projects/new/page.tsx`
- `script_generate` at `apps/worker/tasks/script_generate.py`
- `scene_breakdown` at `apps/worker/tasks/scene_breakdown.py`
- `rag_service.build_context` at `apps/worker/services/rag_service.py`

### Callers Analysis (từ `codegraph_callers`)
- `script_generate`: ≥2 callers (Celery task scheduler + admin replay).
- `scene_breakdown`: ≥1 caller (post-script).

### Callees Analysis (từ `codegraph_callees`)
- `script_generate` calls: `rag_service.build_context`, `select_llm_provider`, `get_channel_assistant` (sẽ cần thay bằng project-aware lookup).

## 3. Các File liên quan và Vai trò
- `apps/web/app/(dashboard)/projects/new/page.tsx`: Page tạo project (cần thêm mode blank).
- `apps/web/components/project-wizard.tsx`: Component wizard cần TẠO MỚI.
- `apps/web/app/(dashboard)/projects/[id]/page.tsx`: Workspace page cần TẠO MỚI.
- `apps/api/routers/projects.py`: Router FastAPI cần TẠO MỚI.
- `apps/api/schemas/projects.py`: Pydantic schema cần TẠO MỚI.
- `apps/api/main.py`: Mount router project.
- `apps/worker/services/project_context.py`: Service build_project_context() cần TẠO MỚI.
- `apps/worker/tasks/script_generate.py`: Sửa để nhận project_id thay vì chỉ assistant_id.
- `apps/worker/tasks/scene_breakdown.py`: Map output sang schema versioned.
- `apps/worker/services/rag_service.py`: Bổ sung blank context fallback.
- `supabase/migrations/0023_projects_foundation.sql`: Tạo bảng projects + project_briefs + project_stage_events.
- `tests/api/test_projects.py`: Tests API + RLS.
- `tests/worker/test_script_generate.py`: Tests task payload + idempotency.

## 4. Dependencies
- **External:** fastapi, pydantic v2, celery, redis, supabase-py, zod.
- **Internal:** `apps.worker.services.rag_service`, `apps.worker.services.select_llm_provider`, `apps.api.schemas.common`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 PowerShell. Mọi verify command phải dùng PowerShell syntax.
- **Line Ending:** CRLF cho mọi file mới.
- **Quy tắc TIER1:** Tier 2 KHÔNG ĐƯỢC tự ý đổi root từ `channel_assistant` sang `project`. Migration phải nullable + deprecation plan.
- **Backward compatibility:** User cũ (channel-based) phải chạy được như cũ.
- **Idempotency:** Tạo project với cùng `(user_id, brief_hash)` phải trả về project_id cũ, không tạo duplicate.
- **Snapshot:** Mọi task ghi input snapshot và output snapshot.
- **Không commit:** KHÔNG push git cho đến khi sếp duyệt (xem `\.claude\memory\no-git-push-until-done.md`).