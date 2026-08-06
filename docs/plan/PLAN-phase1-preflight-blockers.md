# Kế hoạch Triển khai (PLAN): phase1-preflight-blockers

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Sửa 4 blockers chặn đứng pipeline trước khi build Admin Panel (Phase 5+): cleanup SQL function duplicate, fix RLS transcripts leaky, thêm 7 endpoint FastAPI còn thiếu, refactor analysis_task bỏ mock.
- **Giá trị cốt lõi:**
  1. Web UI không còn trả về 500 ở 6 trang chính (`/assistants`, `/jobs/[id]`, `/analysis/[id]`, `/ideas/[id]`, `/projects/new`, `/billing`).
  2. Worker `analysis_channel_task` chạy trên data thật (video + transcript), không phải mock.
  3. Bảo mật: `transcripts` table scope theo assistant thay vì "all authenticated".
  4. Admin Phase 6+ có data thật để test.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Wire-up existing modules
```
Migration 0023:
  ├─ DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT)  -- (signature cũ từ 0006)
  ├─ DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT)  -- (signature cũ)
  ├─ DROP FUNCTION IF EXISTS release_credits(UUID, UUID)  -- (dead function)
  ├─ DROP POLICY "Authenticated users can view transcripts" ON transcripts  -- (leaky)
  └─ CREATE POLICY "Users can view own assistant transcripts" ON transcripts FOR SELECT
       USING (EXISTS (SELECT 1 FROM dna_chunks dc JOIN channel_assistants ca ...))

FastAPI Routers (NEW):
  apps/api/routers/assistants.py    GET/GET-one/DELETE
  apps/api/routers/jobs.py          POST /trigger (enqueue), GET /{id}, GET /recent
  apps/api/routers/analysis.py      GET /{id}, POST /{id}/reanalyze
  apps/api/routers/ideas.py         GET /{id}
  apps/api/routers/channels.py      POST /collect (wrapper YouTubeCollector + enqueue collect_channel_task)

FastAPI Router (UPDATE):
  apps/api/routers/credits.py       + GET /pricing (query credit_pricing table)

Worker (NEW):
  apps/worker/tasks/collect_channel_task.py
    └─ @celery_app.task: query assistant, call YouTubeCollector, insert videos + transcripts

Worker (UPDATE):
  apps/worker/tasks/analysis_task.py
    └─ Bỏ fetch_mock_data, query videos + transcripts từ DB, gọi TranscriptEngine cho video thiếu

Web Proxy (NEW):
  apps/web/app/api/jobs/trigger/route.ts        POST → /api/jobs/trigger
  apps/web/app/api/jobs/recent/route.ts          GET → /api/jobs/recent
  apps/web/app/api/channels/collect/route.ts     POST → /api/channels/collect
  apps/web/app/api/credits/pricing/route.ts      GET → /api/credits/pricing

main.py (UPDATE):
  Thêm 5 routers mới: assistants_router, jobs_router, analysis_router, ideas_router, channels_router
```

### Luồng dữ liệu (Data flow)

**Trước (bị broken):**
```
[Web] AssistantActions → POST /api/jobs/trigger → ❌ 404
```

**Sau Phase 1:**
```
[Web] AssistantActions → POST /api/web/api/jobs/trigger (Next.js proxy)
  → FastAPI POST /api/jobs/trigger  (apps/api/routers/jobs.py)
    → Insert jobs row
    → cm.hold(user_id, job_id, pricing[task_type])
    → switch task_type:
        'deep_analysis' → analyze_channel_task.delay(job_id, assistant_id)
        'idea_generation' → idea_generate_task.delay(job_id, assistant_id)
        'script_generation' → script_generate_task.delay(...)
```

**Analysis task (sau refactor):**
```
analyze_channel_task.run(job_id, assistant_id):
  → query channel_assistants.youtube_url → parse channel_id
  → query videos table WHERE assistant_id  → có sẵn (do collect_channel_task insert)
  → query transcripts table WHERE video_id IN (...)  → có sẵn (do collect_channel_task insert)
  → for video thiếu transcript: TranscriptEngine.get_transcript(video_id) → save to transcripts table
  → chạy 14 outputs với data thật
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Thay thế `/api/projects/start` bằng `/api/channels/collect` (ĐÃ LOẠI một phần)
- **Lý do:** `/api/projects/start` đang chạy production (audit 1.2.B). **GIỮ NGUYÊN** `/api/projects/start`, **THÊM MỚI** `/api/channels/collect` để không break web cũ. Phase 2 sẽ migrate.

### Phương án B — Sửa `analysis_task` in-place (không tạo `collect_channel_task` riêng) (ĐÃ LOẠI)
- **Lý do loại:** `collect_channel_task` cần chạy độc lập (không cần user hold credits). Nếu nhét vào `analysis_task` thì:
  - Không thể retry YouTube API riêng (user phải trả credit).
  - Khó debug.
- **Lý do chọn:** Tách thành 2 task: `collect_channel_task` (chạy YouTube + insert DB) → `analyze_channel_task` (chạy analysis trên data có sẵn).

### Phương án C — Viết tất cả endpoint vào 1 file `apps/api/routers/extra.py` (ĐÃ LOẠI)
- **Lý do loại:** Convention hiện tại là 1 router/feature. Phase này theo convention.

### Phương án D — Dùng Supabase Edge Functions thay vì FastAPI (ĐÃ LOẢI)
- **Lý do loại:** Đã có FastAPI + Celery infrastructure, không cần thêm Deno runtime.

### Lý do chọn phương án hiện tại
- **Compatibility:** `/api/projects/start` vẫn chạy (zero regression). Web proxy routes đã có → backend thêm → web tự chạy.
- **Maintainability:** Tách `collect_channel_task` → debug dễ + retry riêng.
- **Performance:** Không cần OpenAI call cho video chưa có transcript (transcript engine cache).

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | `DROP FUNCTION` 0023 sai signature → RPC client (credit_manager) fail | **Cao** | Step 1 dùng `DROP FUNCTION IF EXISTS hold_credits(uuid, uuid, int)` AND `hold_credits(uuid, int, uuid)` (idempotent). Test trên local DB trước. |
| 2 | `/api/jobs/trigger` cho phép user khác trigger job của user khác (broken authz) | **Cao** | Step 3: query `channel_assistants WHERE id=? AND user_id=current_user` trước khi enqueue. Nếu không match → 404. |
| 3 | `collect_channel_task` không insert `transcripts` → `analysis_task` query rỗng | Trung bình | Step 9: nếu `transcripts` không có → fallback gọi `TranscriptEngine.get_transcript(video_id)` cho từng video. |
| 4 | Web proxy route gọi FastAPI fail không trả error rõ ràng | Thấp | Step 10: catch error, return NextResponse.json với status code từ FastAPI. |
| 5 | Migration 0023 chạy sau 0022 (admin foundation) nhưng không có local DB | Trung bình | Phase 1 chỉ verify cú pháp SQL bằng cách đọc + check `supabase db reset` optional. |
| 6 | Celery worker không pick up task mới (không restart) | Thấp | Ghi chú trong README: restart worker sau Phase 1. |
| 7 | Mount router mới trong main.py sai tên import → app crash | Trung bình | Step 11: thêm từng router, mỗi lần save + reload + smoke test `/docs`. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~600 lines (SQL: 30, Python: 400, TypeScript: 100, 1 file sửa ~30) |
| **Timeline** | 12 steps MSEW, ước tính 6-8 giờ Tier 2 thực thi + self-test |
| **Files touched** | 11 mới (1 SQL + 5 router + 1 worker + 4 web proxy), 2 sửa (main.py + credits.py), 1 refactor (analysis_task.py) |

## 6. Phụ thuộc giữa các Step
- Step 1 (migration) phải xong trước Step 9 (refactor analysis_task) để verify credit hold không fail.
- Step 2-7 (5 routers + 1 update credits) độc lập nhau → Tier 2 có thể parallel nếu cần.
- Step 8 (collect_channel_task) phải xong trước Step 9 (analysis_task refactor dùng DB data).
- Step 10 (4 web proxy) độc lập với backend, có thể parallel với Step 2-8.
- Step 11 (mount routers) là integration, phải sau Step 2-7.
- Step 12 (verify) cuối cùng.