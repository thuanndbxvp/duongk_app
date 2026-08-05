# Lộ trình Phát triển YouTube AI SaaS (Ưu tiên Core YouTube)

Yêu cầu: Xây dựng dự án từ con số 0 dựa trên kiến trúc `prd_v5_enhanced`. Đặc biệt, **đẩy Module User (Auth, Credit, Tier) xuống làm sau cùng**. Trọng tâm ban đầu là xây dựng các tính năng cốt lõi liên quan đến YouTube để thấy kết quả phân tích thực tế càng sớm càng tốt.

## User Review Required

> [!WARNING]
> Việc bỏ qua User/Auth ở giai đoạn đầu có nghĩa là trong các Sprint 1-3, chúng ta sẽ test API thông qua các script giả lập (mock `user_id = 'test-user-id'`) và chạy Celery worker cục bộ. Các tính năng như trừ Credit hay giới hạn Quota theo User sẽ được tắt tạm thời hoặc bypass cho đến Sprint 4.
> Bạn có đồng ý với cách tiếp cận "Test bằng script trước, lắp giao diện và User sau" này không?

## Proposed Roadmap

### Sprint 1: Foundation & YouTube Data Engine (Backend Core)

Mục tiêu: Xây dựng nền tảng Backend vững chắc và cỗ máy thu thập dữ liệu YouTube, bỏ qua hoàn toàn khái niệm "User".

- **1.1. Khởi tạo Monorepo & Database**
  - Tạo cấu trúc: `/apps/api` (FastAPI 0.115+) và `/apps/worker` (Celery 5.4).
  - Khởi tạo thư mục `/packages/shared-types` chứa Pydantic models. Viết script `sync_types.py` (từ Python sang Zod/TS).
  - Viết SQL Migrations (Supabase): Tạo các bảng `youtube_videos_cache`, `transcripts`, `market_research`. Tạm thời KHÔNG cần RLS.
  - Setup `pg_cron` để tự động xoá `transcripts` sau 90 ngày (ToS compliance).
- **1.2. YouTube API Client & Quota System**
  - Implement class `YouTubeClient` xử lý Key Rotation.
  - Tạo bảng `quota_ledger` để track budget (giới hạn 10,000 units/day/key).
- **1.3. Module 1 - Niche Validate (Discovery)**
  - Code pipeline 10 bước. Tích hợp thư viện `pytrends` và Fallback sang SerpAPI.
  - Implement thuật toán Bulkhead (E4) dùng TokenBucket để chống dội request (cascading failure).
  - Implement Redis Cache với lock (stampede prevention) cho API `POST /api/research/validate`.
- **1.4. Module 2A - Deep Collection**
  - Viết logic cào 200 videos/kênh. Gom nhóm API calls: 50 IDs/request cho `videos.list`.
  - Code Formula A0 (Video Filter) loại bỏ Shorts, Live và Formula A2 (Phát hiện Viral nội bộ kênh dùng MAD).
- **1.5. Transcript Engine (3-Tier)**
  - Code luồng Fallback: `youtube-transcript-api` (Tier 1) -> Supadata API (Tier 2) -> tải audio `yt-dlp` và phiên mã bằng `Whisper` (Tier 3).
- *Verify Sprint 1:* Chạy python script gọi thẳng hàm worker, truyền vào ID kênh YouTube và kiểm tra Database xem có tải đủ 200 metadata và top 5 transcripts hay không.

### Sprint 2: Deep Analysis Engine (14 Outputs)

Mục tiêu: Xử lý dữ liệu thô thành 14 Outputs có giá trị (từ thống kê đến NLP).

- **2.1. Cấu trúc Celery Multi-Queue (E2)**
  - Cấu hình `docker-compose.yml` chia 4 pool: `ml_queue` (2 conc, 4GB), `high_queue` (4 conc, 1GB), `io_queue` (8 conc), `normal_queue`.
- **2.2. Deterministic Layer (Outputs 1-4)**
  - Code pure Python (numpy, statistics) cho Metadata, Tags, Performance Reports.
  - Code các công thức: A4 (Optimal Duration), A5 (Consistency Score), A6, A7 (Tag Co-occurrence).
  - Thuật toán tìm Hidden Insights (A12) bằng Chi-square test, sau đó gọi LLM để diễn dịch (narrate).
- **2.3. NLP & Local ML Layer (Outputs 5, 6, 7, 10)**
  - Load model `wonrax/phobert-base-vietnamese-emotion` và `j-hartmann/emotion-...` ở mức Global Singleton trong Celery worker để tránh cold-start.
  - Tích hợp `underthesea` (VN) và `textstat` để tính Pacing Profile (WPM, độ dài câu).
- **2.4. LLM & Vision Layer (Outputs 8, 9, 11, 14)**
  - Viết prompt trích xuất Hook Analysis, Structural Formula, Mimic Rules gọi OpenAI `gpt-4o`.
  - Tích hợp GPT-4o Vision cho Output 14 (Thumbnail Analysis).
  - Code tính năng Versioning cho bảng `channel_deep_analysis` (E7).
- **2.5. RAG Indexing & Embedding (E3 & E6)**
  - Code thuật toán Semantic Chunking cho Transcript.
  - Implement `EmbeddingRouter`: Đếm dấu tiếng Việt (Diacritics). Nếu VN dùng Cohere (1024d), nếu EN dùng OpenAI (ép về dimensions=1024).
  - Setup TTL 90 ngày cho bảng `dna_chunks`.
- *Verify Sprint 2:* Có một file JSON/Record trong DB chứa đầy đủ 14 Outputs cực kỳ chi tiết của kênh mẫu.

### Sprint 3: AI Script Generation & Creative (Máy Tạo Nội Dung)

Mục tiêu: Sinh ra kịch bản chuẩn giọng điệu, kiểm soát chi phí LLM chặt chẽ.

- **3.1. RAG Retrieval**
  - Viết RPC SQL `match_dna_chunks` trên Supabase (Vector Search).
  - Code thuật toán MMR (Maximal Marginal Relevance) trên Python để rerank kết quả, đảm bảo context đa dạng.
- **3.2. Idea Generation (Outputs 12-13)**
  - Dùng thuật toán HDBSCAN cluster các chủ đề của kênh vs chủ đề Trending.
  - Code Formula A14 (Gap Score) để lọc ra các "Untapped Opportunities".
- **3.3. Script Generation & Anti-Slop (E5 & Appendix L)**
  - Ráp prompt sinh kịch bản (Appendix E3) kèm RAG context.
  - Code Regex kiểm tra văn mẫu (Slop) tiếng Việt (Layer 1).
  - Code vòng lặp Retry sinh kịch bản với "Cost Cap" (E5) giới hạn max $0.10/kịch bản.
- **3.4. Scene Breakdown**
  - Phân rã kịch bản thành các Scene (dùng WPM để ước tính thời lượng mỗi Scene).
  - Tự động gọi LLM dịch context tiếng Việt sang keyword tiếng Anh để tìm B-roll trên Pexels.
- *Verify Sprint 3:* Chạy test truyền 1 chủ đề, nhận về 1 script hoàn chỉnh (có phân chia Scene) mang đậm phong cách của kênh mẫu.

### Sprint 4: The Wrapper (User, Auth, Credit & UI)

Mục tiêu: Đóng gói các Engine thành sản phẩm Web SaaS, xử lý bài toán thanh toán/Credit.

- **4.1. Module User & Database Security**
  - Bật Row Level Security (RLS) cho tất cả các bảng.
  - Setup Supabase Auth (Email/Password).
- **4.2. Next.js BFF (Backend-For-Frontend)**
  - Khởi tạo Next.js 15.
  - Viết API Routes trong Next.js làm proxy, lấy JWT token từ cookie người dùng truyền xuống FastAPI. FastAPI dùng PyJWT để verify signature.
- **4.3. Credit System (E1)**
  - Tạo bảng `users`, `jobs`, `credit_transactions`.
  - Viết RPC SQL `partial_commit_credits` để xử lý Hold/Commit/Release nguyên tử (Atomic), triệt tiêu hoàn toàn Race Condition.
- **4.4. Frontend Dashboard & Realtime**
  - Dựng UI nhập URL kênh YouTube.
  - Tích hợp Supabase Realtime lắng nghe thay đổi của bảng `jobs`. Render thanh Progress chi tiết (sub_progress) cho 14 outputs.
  - Dựng màn hình Script Editor (soạn thảo kịch bản và thay đổi B-roll).

## Verification Plan

Vì chúng ta làm Backend/Engine trước, việc Verify sẽ chủ yếu dùng Python Script hoặc Swagger UI (FastAPI docs).

### Automated Tests
- Viết các test script để chạy luồng cào dữ liệu YouTube độc lập mà không cần truyền `user_id` thật.
- Test embedding router trả về đúng Model và kích thước Vector (1024).

### Manual Verification
- Chạy thử luồng `Niche Validate` và kiểm tra dữ liệu cache trong Redis.
- Kích hoạt tiến trình cào 1 kênh mẫu (ví dụ 100 video) và xem DB có được đổ đầy Transcript hay không.
