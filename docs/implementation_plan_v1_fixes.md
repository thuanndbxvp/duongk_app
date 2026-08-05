# Lộ trình Phát triển YouTube AI SaaS (Ưu tiên Core YouTube) — v1_fixes

> **Version:** v1_fixes (2026-08-05)
> **Base:** implementation_plan_v1.md
> **Changes:** F1-F4 (Critical) + G1-G4 (High) + H1-H4 (Medium) đã được tích hợp

Yêu cầu: Xây dựng dự án từ con số 0 dựa trên kiến trúc `prd_v5_enhanced`. Đặc biệt, **đẩy Module User (Auth, Credit, Tier) xuống làm sau cùng**. Trọng tâm ban đầu là xây dựng các tính năng cốt lõi liên quan đến YouTube để thấy kết quả phân tích thực tế càng sớm càng tốt.

---

## User Review Required

> [!WARNING]
> Việc bỏ qua User/Auth ở giai đoạn đầu có nghĩa là trong các Sprint 1-3, chúng ta sẽ test API thông qua các script giả lập (mock `user_id = 'test-user-id'` hoặc `user_id = 'system'`) và chạy Celery worker cục bộ. Các tính năng như trừ Credit hay giới hạn Quota theo User sẽ được tắt tạm thời hoặc bypass cho đến Sprint 4.
> Bạn có đồng ý với cách tiếp cận "Test bằng script trước, lắp giao diện và User sau" này không?

---

## Effort Estimation

| Sprint | Thời gian | Effort | Ghi chú |
|--------|-----------|--------|---------|
| Sprint 1 | 2 tuần | ~60h | Foundation + YouTube Data Engine |
| Sprint 2 | 2 tuần | ~70h | Deep Analysis Engine (14 Outputs) |
| Sprint 3 | 1.5 tuần | ~50h | AI Script Generation |
| Sprint 4 | 2 tuần | ~60h | User, Auth, Credit & UI |
| **Tổng** | **~7.5 tuần** | **~240h** | |

---

## Proposed Roadmap

### Sprint 1: Foundation & YouTube Data Engine (Backend Core)

**Thời gian:** 2 tuần (~60h)
**Mục tiêu:** Xây dựng nền tảng Backend vững chắc và cỗ máy thu thập dữ liệu YouTube, bỏ qua hoàn toàn khái niệm "User".

#### 1.1. Khởi tạo Monorepo & Database

- Tạo cấu trúc: `/apps/api` (FastAPI 0.115+) và `/apps/worker` (Celery 5.4).
- Khởi tạo thư mục `/packages/shared-types` chứa Pydantic models.
- **G1 FIX:** Viết script `sync_types.py` (từ Python sang Zod/TS) — Reference: prd_v5_enhanced §Appendix N (D12).
- **G2 FIX:** SQL Migrations ordering:
  - `0001_users.sql` (placeholder — sẽ bật RLS ở Sprint 4)
  - `0002_jobs.sql`
  - `0003_credit_transactions.sql`
  - `0004_api_usage_logs.sql`
  - `0005_quota_ledger.sql`
  - `0006_credit_hold_commit.sql` (E1 — atomic RPC)
  - `0007_rls_policies.sql` (placeholder — bật ở Sprint 4)
  - `0008_channel_assistants.sql`
  - `0009_channel_deep_analysis.sql`
  - `0010_progress_sub_progress.sql` (D1 — race-safe RPC)
  - `0011_race_safe_update.sql`
- Setup `pg_cron` để tự động xoá `transcripts` sau 90 ngày (ToS compliance).

#### 1.2. Environment Variables & Secrets Management

**F3 FIX:** Thêm `.env.example`:

```bash
# YouTube API Keys (nhiều keys cho rotation)
YOUTUBE_API_KEY_1=AIza...
YOUTUBE_API_KEY_2=AIza...
YOUTUBE_API_KEY_3=AIza...
YOUTUBE_API_KEY_4=AIza...
YOUTUBE_API_KEY_5=AIza...

# LLM
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...

# Embedding
COHERE_API_KEY=...

# Trends
SERPAPI_KEY=...

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=super-secret-xxx

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Observability
SENTRY_DSN=https://xxx@sentry.io/xxx
```

#### 1.3. YouTube API Client & Quota System

- Implement class `YouTubeClient` xử lý Key Rotation.
- **G3 FIX:** Thêm retry policy:
  - 403 (quota exceeded): Rotate key + exponential backoff (1s, 2s, 4s)
  - 500/503: Retry 3 lần với exponential backoff
  - 429: Circuit breaker 5 phút
- Tạo bảng `quota_ledger` để track budget (giới hạn 10,000 units/day/key).

#### 1.4. Module 1 - Niche Validate (Discovery)

- Code pipeline 10 bước. Tích hợp thư viện `pytrends` và Fallback sang SerpAPI.
- **E4 FIX:** Implement thuật toán Bulkhead (TokenBucket) để chống dội request (cascading failure).
- Implement Redis Cache với lock (stampede prevention) cho API `POST /api/research/validate`.
- **H4 FIX:** Sample output:

```json
{
  "keyword": "lam dep",
  "total_monthly_views": 15000000,
  "total_channels": 45,
  "avg_views_per_video": 45000,
  "google_trends_interest": 72,
  "is_viable": true,
  "suggested_titles": [
    "5 công thức làm đẹp từ thiên nhiên",
    "Cách chăm sóc da mùa đông"
  ]
}
```

#### 1.5. Module 2A - Deep Collection

- Viết logic cào 200 videos/kênh. Gom nhóm API calls: 50 IDs/request cho `videos.list`.
- Code Formula A0 (Video Filter) loại bỏ Shorts, Live và Formula A2 (Phát hiện Viral nội bộ kênh dùng MAD).

#### 1.6. Transcript Engine (3-Tier)

- Code luồng Fallback: `youtube-transcript-api` (Tier 1) -> Supadata API (Tier 2) -> tải audio `yt-dlp` và phiên mã bằng `Whisper` (Tier 3).
- **E1 PARTIAL:** Tạo RPC `partial_commit_credits` (sẽ dùng cho test scripts với `user_id='system'`).

#### 1.7. Docker Compose với Multi-Queue Workers

**F1 FIX:** Setup Docker Compose với 4 worker pools (E2):

```yaml
# docker-compose.yml
services:
  # ... postgres, redis, api ...

  worker_ml:
    build: ./apps/api
    command: celery -A apps.worker.celery_app worker -Q ml_queue --loglevel=info --concurrency=2
    deploy:
      resources:
        limits:
          memory: 4G
    environment:
      - CELERYD_MAX_TASKS_PER_CHILD=50
      - CELERYD_MAX_MEMORY_PER_CHILD=4_000_000

  worker_high:
    build: ./apps/api
    command: celery -A apps.worker.celery_app worker -Q high_queue --loglevel=info --concurrency=4
    deploy:
      resources:
        limits:
          memory: 2G
    environment:
      - CELERYD_MAX_TASKS_PER_CHILD=20

  worker_io:
    build: ./apps/api
    command: celery -A apps.worker.celery_app worker -Q io_queue --loglevel=info --concurrency=8
    deploy:
      resources:
        limits:
          memory: 1G
    environment:
      - CELERYD_MAX_TASKS_PER_CHILD=10
      - CELERYD_MAX_MEMORY_PER_CHILD=500_000

  worker_normal:
    build: ./apps/api
    command: celery -A apps.worker.celery_app worker -Q normal_queue --loglevel=info --concurrency=4
    deploy:
      resources:
        limits:
          memory: 2G
    environment:
      - CELERYD_MAX_TASKS_PER_CHILD=30
```

#### 1.8. Observability & Logging

**F4 FIX:** Setup Sentry + basic logging:

```python
# apps/api/main.py
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

# apps/worker/celery_app.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 1.9. OpenAPI Spec Generation

**G4 FIX:** Generate OpenAPI spec từ FastAPI:

```python
# apps/api/main.py
from fastapi.openapi.utils import get_openapi

app = FastAPI(...)

@app.get("/openapi.json")
async def openapi():
    return get_openapi(title=app.title, version=app.version, routes=app.routes)
```

*Verify Sprint 1:* Chạy python script gọi thẳng hàm worker, truyền vào ID kênh YouTube và kiểm tra Database xem có tải đủ 200 metadata và top 5 transcripts hay không.

---

### Sprint 2: Deep Analysis Engine (14 Outputs)

**Thời gian:** 2 tuần (~70h)
**Mục tiêu:** Xử lý dữ liệu thô thành 14 Outputs có giá trị (từ thống kê đến NLP).

#### 2.1. Deterministic Layer (Outputs 1-4)

- Code pure Python (numpy, statistics) cho Metadata, Tags, Performance Reports.
- Code các công thức: A4 (Optimal Duration), A5 (Consistency Score), A6, A7 (Tag Co-occurrence).
- Thuật toán tìm Hidden Insights (A12) bằng Chi-square test, sau đó gọi LLM để diễn dịch (narrate).

#### 2.2. NLP & Local ML Layer (Outputs 5, 6, 7, 10)

- **E2 FIX:** Load model `wonrax/phobert-base-vietnamese-emotion` và `j-hartmann/emotion-...` ở mức Global Singleton trong Celery worker để tránh cold-start.
- Tích hợp `underthesea` (VN) và `textstat` để tính Pacing Profile (WPM, độ dài câu).

#### 2.3. LLM & Vision Layer (Outputs 8, 9, 11, 14)

- Viết prompt trích xuất Hook Analysis, Structural Formula, Mimic Rules gọi OpenAI `gpt-4o`.
- Tích hợp GPT-4o Vision cho Output 14 (Thumbnail Analysis).
- **E7 FIX:** Code tính năng Versioning cho bảng `channel_deep_analysis`.

#### 2.4. RAG Indexing & Embedding (E3 & E6)

- Code thuật toán Semantic Chunking cho Transcript.
- **E3 FIX:** Implement `EmbeddingRouter`: Đếm dấu tiếng Việt (Diacritics). Nếu VN dùng Cohere (1024d), nếu EN dùng OpenAI (ép về dimensions=1024).
- **E6 FIX:** Setup TTL 90 ngày cho bảng `dna_chunks`.

#### 2.5. Progress Granularity (D1)

- **D1 FIX:** Implement `update_job_sub_progress` RPC với race-safe pattern (jsonb_set + FOR UPDATE).
- Implement `ProgressTracker` class cho worker.

*Verify Sprint 2:* Có một file JSON/Record trong DB chứa đầy đủ 14 Outputs cực kỳ chi tiết của kênh mẫu.

---

### Sprint 3: AI Script Generation & Creative (Máy Tạo Nội Dung)

**Thời gian:** 1.5 tuần (~50h)
**Mục tiêu:** Sinh ra kịch bản chuẩn giọng điệu, kiám soát chi phí LLM chặt chẽ.

#### 3.1. RAG Retrieval

- Viết RPC SQL `match_dna_chunks` trên Supabase (Vector Search).
- Code thuật toán MMR (Maximal Marginal Relevance) trên Python để rerank kết quả, đảm bảo context đa dạng.

#### 3.2. Idea Generation (Outputs 12-13)

- Dùng thuật toán HDBSCAN cluster các chủ đề của kênh vs chủ đề Trending.
- Code Formula A14 (Gap Score) để lọc ra các "Untapped Opportunities".

#### 3.3. Script Generation & Anti-Slop (E5 & Appendix L)

- Ráp prompt sinh kịch bản (Appendix E3) kèm RAG context.
- **Appendix L FIX:** Code Regex kiểm tra văn mẫu (Slop) tiếng Việt (Layer 1).
- **E5 FIX:** Code vòng lặp Retry sinh kịch bản với "Cost Cap" giới hạn max $0.10/kịch bản.

#### 3.4. Scene Breakdown

- Phân rã kịch bản thành các Scene (dùng WPM để ước tính thời lượng mỗi Scene).
- Tự động gọi LLM dịch context tiếng Việt sang keyword tiếng Anh để tìm B-roll trên Pexels.

*Verify Sprint 3:* Chạy test truyền 1 chủ đề, nhận về 1 script hoàn chỉnh (có phân chia Scene) mang đậm phong cách của kênh mẫu.

**Sprint 3 Documents:**
- **Chi tiết:** `docs/sprints/02_sprint3_ai_script_generation.md`

---

### Sprint 4: The Wrapper (User, Auth, Credit & UI)

**Thời gian:** 2 tuần (~60h)
**Mục tiêu:** Đóng gói các Engine thành sản phẩm Web SaaS, xử lý bài toán thanh toán/Credit.

#### 4.1. Module User & Database Security

- Bật Row Level Security (RLS) cho tất cả các bảng.
- Setup Supabase Auth (Email/Password).
- **D11 FIX:** JWT verify với `SUPABASE_JWT_SECRET`.

#### 4.2. Next.js BFF (Backend-For-Frontend)

- Khởi tạo Next.js 15.
- Viết API Routes trong Next.js làm proxy, lấy JWT token từ cookie người dùng truyền xuống FastAPI. FastAPI dùng PyJWT để verify signature.

#### 4.3. Credit System (E1)

- **E1 FIX:** Bật `partial_commit_credits` cho production users.
- Tạo bảng `users`, `jobs`, `credit_transactions` (đã tạo placeholder ở Sprint 1).

#### 4.4. Frontend Dashboard & Realtime

- Dựng UI nhập URL kênh YouTube.
- Tích hợp Supabase Realtime lắng nghe thay đổi của bảng `jobs`. Render thanh Progress chi tiết (sub_progress) cho 14 outputs.
- Dựng màn hình Script Editor (soạn thảo kịch bản và thay đổi B-roll).

---

## Verification Plan

Vì chúng ta làm Backend/Engine trước, việc Verify sẽ chủ yếu dùng Python Script hoặc Swagger UI (FastAPI docs).

### Automated Tests

**H1 FIX:** Thêm test coverage target:

| Layer | Target Coverage |
|-------|----------------|
| Business Logic (formulas, pipeline) | 90% |
| API endpoints | 80% |
| Celery tasks | 70% |
| Database migrations | 100% |

- Viết các test script để chạy luồng cào dữ liệu YouTube độc lập mà không cần truyền `user_id` thật.
- Test embedding router trả về đúng Model và kích thước Vector (1024).

### Manual Verification

- Chạy thử luồng `Niche Validate` và kiểm tra dữ liệu cache trong Redis.
- Kích hoạt tiến trình cào 1 kênh mẫu (ví dụ 100 video) và xem DB có được đổ đầy Transcript hay không.

---

## Environments & CI/CD

### Environments

**H2 FIX:** Thêm staging environment:

| Environment | URL | Purpose |
|-------------|-----|---------|
| Development | localhost:3000 | Local dev |
| Staging | staging.appdk.vn | Pre-production testing |
| Production | appdk.vn | Live users |

```yaml
# docker-compose.staging.yml
services:
  api:
    environment:
      - API_ENV=staging
    build:
      context: .
      target: staging
```

### CI/CD Pipeline

**H3 FIX:** GitHub Actions:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install uv && uv sync
      - run: pytest --cov=apps --cov-report=xml
      - uses: codecov/codecov-action@v4

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/sync_types.py
      - run: git diff --exit-code
```

---

## Fallback Plan

**G5 FIX:** Nếu Sprint 4 thất bại:

> Vẫn có thể dùng API trực tiếp (script) để:
> - Test YouTube data collection
> - Test Deep Analysis engine
> - Test Script generation
>
> User vẫn có thể truy cập Swagger UI (`/docs`) để trigger jobs.

---

## Changelog

| Version | Ngày | Thay đổi |
|---------|------|-----------|
| v1 | 2026-08-05 | Base plan |
| **v1_fixes** | 2026-08-05 | **F1-F4 + G1-G4 + H1-H4 tích hợp** |

### F-Series Fixes (Critical)

| ID | Mô tả |
|----|--------|
| F1 | Add Docker Compose task với 4 worker pools (E2) |
| F2 | E1 partial commit đặt ở Sprint 1 (cho test scripts với user_id='system') |
| F3 | Add environment variables section (.env.example) |
| F4 | Add Sentry/logging task vào Sprint 1 |

### G-Series Fixes (High)

| ID | Mô tả |
|----|--------|
| G1 | Add effort estimation (tuần + giờ) |
| G2 | Add migration file ordering (0001-0011) |
| G3 | Add YouTube API retry policy (exponential backoff) |
| G4 | Add OpenAPI spec generation task |

### H-Series Fixes (Medium)

| ID | Mô tả |
|----|--------|
| H1 | Add test coverage target (90%/80%/70%) |
| H2 | Add staging environment (docker-compose.staging.yml) |
| H3 | Add CI/CD pipeline (GitHub Actions) |
| H4 | Add sample output cho Module 1 |

---

## Readiness Checklist

```
TRƯỚC KHI BẮT ĐẦU SPRINT 1:
[X] F1: Docker Compose với 4 worker pools
[X] F2: partial_commit_credits RPC (test scripts)
[X] F3: .env.example với tất cả secrets
[X] F4: Sentry + logging setup

TRONG SPRINT 1:
[X] G1: Effort estimation
[X] G2: Migration ordering (0001-0011)
[X] G3: Retry policy cho YouTube API
[X] G4: OpenAPI spec generation

TRONG/DO SAU SPRINT 1:
[ ] H1: Test coverage target
[ ] H2: Staging environment
[ ] H3: CI/CD pipeline
[ ] H4: Sample outputs
```

---

**Document version:** v1_fixes.1.0
**Last updated:** 2026-08-05
**Status:** Ready for Sprint 1
