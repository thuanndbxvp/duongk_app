# Kế hoạch Triển khai (PLAN): Phase 01 — Project foundation & Blank Project

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Cho phép user tạo project mới từ "blank topic" không cần YouTube channel, đồng thời giữ backward compatibility với flow cũ (channel cloning).
- **Giá trị cốt lõi:** Mở cửa cho người dùng mới (chưa có channel), đơn giản hoá onboarding, đặt nền tảng `project` làm root entity xuyên suốt 11 phase.

## 2. Kiến trúc lựa chọn (Architecture)
- **Patterns/Design:**
  - **Repository-style service layer** cho `project_context.py`.
  - **Nullable FK** + **adapter pattern** cho transition từ `channel_assistant` sang `project`.
  - **Pydantic v2 schema** ở cả backend (Python) và frontend (Zod mirror) để validate 1 lần, dùng 2 nơi.
  - **Idempotency key** dạng `project_idempotency_key(user_id, brief_hash)`.
- **Mô tả luồng đi:**

```text
User (Next.js wizard)
  → POST /api/projects (blank | clone_channel)
  → FastAPI router validates payload
  → Supabase: insert projects + project_briefs (idempotent)
  → enqueue Celery task concept/outline/script/scene (gắn project_id)
  → Worker: project_context.build_project_context()
       → rag_service.build_context(blank_fallback OR channel_DNA)
  → script_generate → scene_breakdown → trả scene contracts v1
  → Project workspace hiển thị stage + job progress
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)
- **Phương án A — Big-bang rewrite root từ assistant sang project (ĐÃ LOẠI):** Phá vỡ mọi user cũ đang chạy production. Vi phạm nguyên tắc TIER1 "không đập đi xây lại".
- **Phương án B — Để assistant là root, thêm project_id nullable (CHỌN MỘT PHẦN):** Migration tạo bảng `projects` mới, giữ `channel_assistants` nguyên. Project_id nullable trên mọi bảng con (jobs, scripts, scenes). Lookup adapter tự chọn nguồn.
- **Phương án C — Phase 01 chỉ thêm UI blank, không đổi DB (ĐÃ LOẠI):** Wizard sẽ phải hard-code flow channel; phá sạch kế hoạch dài hạn 11 phase.

**Lý do chọn B:**
- Backward compatibility triệt để.
- Migration nullable, adapter pattern → refactor dần ở phase sau.
- Phù hợp Windows + PowerShell + Supabase (PostgreSQL + RLS dễ triển khai incremental).
- Test idempotency có thể làm ngay vì key dựa trên `user_id + brief_hash`.

## 4. Đánh giá rủi ro (Risk Assessment)

| Rủi ro | Mức độ | Giảm thiểu |
|---|---|---|
| Đổi root từ assistant sang project phá API cũ | Cao | Migration nullable + adapter + deprecation plan. Mọi call site cũ vẫn dùng channel_assistant_id; chỉ flow mới dùng project_id. |
| Brief lưu JSONB không có schema_version → drift | Trung bình | Pydantic schema có `schema_version: Literal[1]`. Output snapshot lưu cùng schema_version. |
| Idempotency sai → user bấm 2 lần tạo 2 project | Trung bình | `brief_hash = sha256(canonical_json(brief))`. Lookup trước khi insert. Unique constraint `(user_id, brief_hash)`. |
| RLS bypass nếu service_role_key lộ | Cao | Service_role key chỉ ở server, KHÔNG BAO GIỜ ở client. Mọi route đều dùng user JWT + RLS. Audit log truy cập. |
| Job retry sinh duplicate scene contracts | Trung bình | Idempotency key `project_id:task_name:brief_version`. Trước khi enqueue, check job đã `succeeded` cho cùng key. |
| Frontend wizard gọi endpoint cũ → mất data | Thấp | Wizard mới ở route `/projects/new`, route cũ `/channels/new` giữ nguyên. Wizard detect mode từ URL param. |

## 5. Dự kiến nỗi lực (Estimation)
- **Estimated LOC:** ~900 lines (SQL migration ~200, Python backend ~450, Next.js ~250).
- **Timeline:** 9 micro-steps, ước tính 3–4 ngày cho Tier 2 (1 ngày train + 3 ngày code/test).

## 6. Phụ thuộc (Dependencies)
- **Phase phụ thuộc:** Không (Phase 01 là root).
- **Phase phụ thuộc vào:** Phase 02, 03, 04, 05, 06, 08, 09, 10, 11.
- **External services:** Supabase (PostgreSQL + RLS + Storage), Redis (Celery broker), OpenAI/Anthropic API (cho LLM script).

## 7. Tiêu chí thành công (Phase 01 done khi)
- User tạo project blank không cần channel URL.
- User cũ vẫn chạy flow channel-based.
- Project reload không mất brief.
- Job retry idempotent.
- RLS chặn đúng user khác đọc/sửa.
- Tests pass với coverage ≥80% cho module mới.