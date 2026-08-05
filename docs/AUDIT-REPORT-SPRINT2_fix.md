# Hoàn thiện Sprint 2: Deep Analysis, RAG Storage & Progress Tracking

Dựa trên Báo cáo Audit Sprint 2, dự án đã đạt 60% tiến độ nhưng vẫn còn thiếu một số module cốt lõi để hệ thống có thể chạy hoàn chỉnh. Bản kế hoạch này sẽ xử lý triệt để 7 file còn thiếu.

*(Lưu ý: Các package như `openai`, `cohere`, `supabase`... đã có sẵn trong `requirements.txt` từ trước, nên không cần cài lại).*

## User Review Required

> [!WARNING]
> **Celery Task Integration:** Việc tích hợp toàn bộ các Layer (Deterministic, NLP, LLM, Vision, RAG) vào chung một `analysis_task.py` (Worker) sẽ tạo ra một luồng xử lý rất dài. Tôi sẽ import trực tiếp các analyzer class vào task này để chạy nối tiếp (hoặc song song nếu có thể).
>
> **Database RPC:** Sếp nhớ phải chạy lệnh Push/Reset migration cho các file `.sql` mới để Progress Tracker hoạt động không bị lỗi.

## Open Questions

> [!IMPORTANT]
> Đối với **Output 12 (Hidden Insights)** trong file `insights.py`, sếp muốn phân tích tương quan bằng thuật toán `scipy` (Chi-square test) kết hợp LLM để suy luận, hay chỉ cần ném toàn bộ data cho LLM tự rút ra insight? (Hiện tại tôi sẽ kết hợp cả hai để đảm bảo độ chính xác).

## Proposed Changes

---

### 1. Database Migrations (Fix P0)

#### [NEW] [0014_progress_sub.rpc.sql](file:///d:/appDK/supabase/migrations/0014_progress_sub.rpc.sql)
- Tạo hàm RPC `update_job_sub_progress(p_job_id, p_task_name, p_status, p_message)` giúp ProgressTracker cập nhật trạng thái an toàn (tránh race-condition bằng `FOR UPDATE`).

*(Lưu ý: Migration `0012_analysis_versions.sql` đã được tạo trong một phiên làm việc trước đó, và TTL 90 ngày của `0013` đã có sẵn ở `0010_dna_chunks.sql` nên sẽ bỏ qua 0013).*

---

### 2. Core Modules (Fix P0 & P1)

#### [NEW] [apps/api/modules/rag/storage.py](file:///d:/appDK/apps/api/modules/rag/storage.py)
- Viết class `RAGStorage` sử dụng thư viện `supabase-py` để lưu hàng loạt (upsert/insert) các vector embedding vào bảng `dna_chunks`.
- Tích hợp vào API Router của RAG.

#### [NEW] [apps/api/modules/analysis/insights.py](file:///d:/appDK/apps/api/modules/analysis/insights.py)
- Cài đặt hàm `find_hidden_insights` (Output 12).
- Sử dụng `scipy.stats` tính tương quan (ví dụ: độ dài video với lượng view).
- Gửi kết quả thống kê cho LLM để suy luận ra insight dễ hiểu.

#### [NEW] [apps/api/modules/llm/prompts.py](file:///d:/appDK/apps/api/modules/llm/prompts.py)
- Tách toàn bộ các câu lệnh Prompt (hardcode) từ `analyzer.py` sang file này thành các hằng số rõ ràng để dễ bảo trì và tái sử dụng.

---

### 3. Celery Integration & Documentation

#### [MODIFY] [apps/worker/tasks/analysis_task.py](file:///d:/appDK/apps/worker/tasks/analysis_task.py)
- Hoàn thiện bộ khung (skeleton) hiện tại.
- Import và gọi trực tiếp `GPTNLPAnalyzer`, `LLMAnalyzer`, `ThumbnailAnalyzer`, `SemanticChunker`, và `Embedder` cho từng step của 14 outputs.
- Bắt lỗi và gửi `ProgressTracker.fail()` nếu có module bị sập.

#### [NEW] [docs/sprints/02_sprint2_youtube_collection.md](file:///d:/appDK/docs/sprints/02_sprint2_youtube_collection.md)
- Bổ sung tài liệu Planning cho Sprint 2 (ghi chép lại tất cả Output và kiến trúc của Deep Analysis Engine).

---

## Verification Plan

### Automated Tests
- Chạy toàn bộ test suite hiện có: `pytest tests/ -v`.
- Syntax check cho file Python `analysis_task.py` mới.

### Manual Verification
- Sếp apply file SQL migration bằng `supabase db push`.
- Nếu có backend đang chạy, test thử một luồng phân tích đơn giản (hoặc trigger worker bằng script).
