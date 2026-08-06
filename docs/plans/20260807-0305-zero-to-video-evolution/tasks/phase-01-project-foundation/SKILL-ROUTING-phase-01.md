# Phân bổ Kỹ năng (SKILL-ROUTING): Phase 01 — Project foundation & Blank Project

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 01 chủ yếu làm việc với database schema, FastAPI router, Pydantic validation, Next.js wizard, và một ít Celery worker. Đây là phase "foundation" nên ưu tiên:
- Schema an toàn + RLS (vì có dữ liệu user thật).
- Validation payload chặt (Pydantic v2 + Zod).
- UI wizard đơn giản, dễ test.
- Không chạm AI generation trong phase này (chỉ wire-up).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Tạo migration `projects` + RLS | `databases` | `backend-development` | `debugging` | Schema là xương sống; lỗi schema phá toàn bộ downstream. |
| Step 2 | Pydantic schemas `Project`, `Brief`, `ApprovalState` | `backend-development` | `databases` | `debugging` | Pydantic v2 + cross-check với constraint DB. |
| Step 3 | FastAPI router `/api/projects` | `backend-development` | `databases` | `debugging` | API CRUD + RLS check. |
| Step 4 | Service `project_context.build_project_context()` | `backend-development` | `planning` | `debugging` | Logic kết hợp brief + optional channel DNA. |
| Step 5 | Sửa `script_generate.py` nhận project_id | `backend-development` | `planning` | `debugging` | Celery task signature thay đổi, idempotency key đổi. |
| Step 6 | Sửa `scene_breakdown.py` schema versioned output | `backend-development` | `planning` | `debugging` | Output JSONB cần có schema_version. |
| Step 7 | Next.js wizard UI | `frontend-development` | `ui-styling` | `aesthetic` | Form + mode toggle. |
| Step 8 | Project workspace page | `frontend-development` | `ui-styling` | `aesthetic` | Stage + job progress UI. |
| Step 9 | Tests API/RLS/task | `testing-protocol` | `debugging-protocol` | `debugging` | Bắt buộc ≥80% coverage. |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `anti-hallucination`: Mỗi khi Tier 2 sửa code phải grep/CodeGraph xác nhận đúng file + đúng caller. KHÔNG được "đoán" signature.
- `debugging-protocol`: Khi verify fail, KHÔNG tự sửa code ngoài scope; ghi BLOCKERS.md và dừng.
- `code-review`: Trước khi giao AUDIT-REPORT, Tier 2 tự review.
- `repomix-usage`: Trước khi code, sinh CONTEXT_BUNDLE.md bằng repomix.

## 4. Kỹ năng CẤM (Forbidden Skills)
- `refactor`: Phase 01 không phải lúc refactor; CẤM gọi skill refactor.
- `skill/optimize`: Phase 01 chưa cần tối ưu.