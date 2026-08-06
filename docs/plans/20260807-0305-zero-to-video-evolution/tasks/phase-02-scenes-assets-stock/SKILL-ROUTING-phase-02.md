# Phân bổ Kỹ năng (SKILL-ROUTING): Phase 02 — Scene Studio

## 1. Chiến lược tổng thể
Phase 02 chủ yếu làm việc với: schema asset + scene, provider contract abstraction, R2 presigned URL, scene editor UI. Đây là phase "core media" nên ưu tiên:
- Provider contract chặt (interface rõ ràng).
- Source immutability + variant tracking.
- R2 signed URL ngắn hạn.
- Không scrape — chỉ dùng API chính thức của Pexels.

## 2. Bảng Phân bổ theo Step

| MSEW Step | Task | Primary Skill | Reference Skill | Fallback Skill | Lý do |
|---|---|---|---|---|---|
| Step 1 | Migration `project_scenes` + `assets` + `asset_variants` | `databases` | `backend-development` | `debugging` | Schema với RLS. |
| Step 2 | Pydantic schemas assets | `backend-development` | `databases` | `debugging` | Validation MIME, size, duration. |
| Step 3 | Provider contract base + 3 adapter (Upload, Pexels, Local) | `backend-development` | `planning` | `debugging` | Interface ổn định. |
| Step 4 | FastAPI router assets (CRUD + signed URL) | `backend-development` | `databases` | `debugging` | API với RLS. |
| Step 5 | Materialize task (remote → R2) | `backend-development` | `databases` | `debugging` | Idempotent. |
| Step 6 | Scene editor UI (Scene Studio) | `frontend-development` | `ui-styling` | `aesthetic` | Drag-drop, asset drawer. |
| Step 7 | Asset drawer UI | `frontend-development` | `ui-styling` | `aesthetic` | Upload + search + preview. |
| Step 8 | Tests provider contract + RLS + signed URL | `testing-protocol` | `debugging-protocol` | `debugging` | Coverage. |

## 3. Cross-cutting Skills
- `anti-hallucination`: Mỗi provider adapter phải có interface rõ ràng; Tier 2 không tự ý thêm method ngoài contract.
- `debugging-protocol`: Khi verify fail, KHÔNG tự sửa code ngoài scope.
- `code-review`: Trước khi AUDIT-REPORT.

## 4. Forbidden Skills
- `refactor`: Phase 02 không refactor `scene-timeline.tsx`; chỉ wrap hoặc tạo mới.
- Skill `payment-integration`: Không liên quan.