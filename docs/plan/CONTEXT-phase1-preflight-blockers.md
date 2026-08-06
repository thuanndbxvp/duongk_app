# Bối cảnh Hệ thống (CONTEXT): phase1-preflight-blockers

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Mục tiêu Phase 1:** Fix 4 blockers chặn đứng pipeline trước khi build Admin Panel (Phase 5+) và các feature UI user-facing.
- **CodeGraph status:** indexed (đã query thành công qua MCP `user-codegraph` ở Phase 5).

## 2. Codebase Analysis (via CodeGraph MCP — `codegraph_context` với task: FastAPI router + credit_manager + migration 0020)

### Discovery
- `apps/api/services/credit_manager.py` có 2 RPC calls: `hold_credits(p_user_id, p_amount, p_job_id)` (signature MỚI từ 0020) và `partial_commit_credits(p_job_id, p_final_amount)` (signature MỚI). Tuy nhiên migration `0006_credit_hold_commit.sql` vẫn định nghĩa function cũ với signature `(p_user_id, p_job_id, p_amount)` (ĐẢO THAM SỐ) → Postgres sẽ throw "function hold_credits(uuid, uuid, int) does not exist" khi RPC call theo signature mới nhưng vẫn còn function cũ ở plan cache.
- `apps/api/main.py` mount 12 routers từ `apps/api/routers/*` và `apps/api/modules/*`. **KHÔNG có** router `/api/assistants`, `/api/jobs/trigger`, `/api/jobs/{id}`, `/api/analysis/{id}`, `/api/ideas/{id}`, `/api/channels/collect` (note: `/api/collect/channel` ở module_2a đã có, khác `/api/channels/collect` mà web đang gọi), `/api/credits/pricing`.
- `apps/web/app/api/assistants/route.ts` (line 12) gọi `apiFetch('/api/assistants')` → 404 vì backend không có.
- `apps/web/app/api/jobs/[id]/route.ts` (line 17) gọi `apiFetch('/api/jobs/${id}')` → 404.
- `apps/worker/tasks/analysis_task.py:fetch_mock_data()` (line 19-20) trả 5 video fake cứng + transcripts `["Hello world"] * 5` — analysis 14 outputs chạy trên data rác.
- `supabase/migrations/0011_transcripts_cron.sql` tạo table `transcripts(video_id, text_content, raw_data, fetched_at, expires_at)` + `cron.schedule('transcript-cleanup', '0 3 * * *', ...)`. KHÔNG thấy policy RLS trong file này. (Tuy nhiên audit 1.4 ghi nhận có policy leaky "Authenticated users can view transcripts" — kiểm tra `0015_rls_policies.sql` và `0019_enable_rls_policies.sql` đã confirm policy này tồn tại.)

### Related Symbols (đã xác nhận qua CodeGraph)
- `CreditManager` class at `apps/api/services/credit_manager.py:43`
- `hold` method at `apps/api/services/credit_manager.py:64` — signature `(self, user_id: str, job_id: str, amount: int)`
- `adjust` method at `apps/api/services/credit_manager.py:85` — calls RPC `partial_commit_credits(p_job_id, p_final_amount)`
- `start_project` at `apps/api/routers/projects.py:19` — caller duy nhất của `hold()`
- `analyze_channel_task` at `apps/worker/tasks/analysis_task.py:22` — dùng `fetch_mock_data()`
- `YouTubeCollector` at `apps/api/modules/module_2a/service.py` — class thật, đã được mount qua `/api/collect/channel`
- `TranscriptEngine` at `apps/api/modules/transcript/engine.py` — class thật, đã được mount qua `/api/transcript`

### Callers Analysis
- `hold()` callers: **1** (`start_project` only)
- `start_project` callers: HTTP route `POST /api/projects/start`
- `analyze_channel_task.delay()` callers: `start_project` line cuối
- `YouTubeCollector.collect_channel_videos()` callers: **1** (chỉ `apps/api/modules/module_2a/routes.py:34`)
- `TranscriptEngine.get_transcript()` callers: **1** (chỉ `apps/api/modules/transcript/routes.py:50`)

### Callees Analysis
- `start_project()` calls:
  - `CreditManager().hold(...)` (line 60)
  - `get_supabase_admin().table(...)` (channel_assistants.insert, jobs.insert, jobs.update)
  - `analyze_channel_task.delay(...)` (Celery dispatch)
  - `re.search(...)` (parse YouTube URL)
- `analyze_channel_task.run()` calls:
  - `ProgressTracker(...)`
  - `fetch_mock_data()` ← STUB
  - 8 analyzers + chunker + embedder + RAGStorage

## 3. Các File liên quan và Vai trò

### Backend (apps/api)
- `apps/api/main.py:1` — App FastAPI + 12 router registration. Phase này sẽ thêm 6-7 routers mới.
- `apps/api/routers/credits.py:1` — đã có `/credits/balance` + `/credits/transactions`. Phase này thêm `/credits/pricing`.
- `apps/api/routers/projects.py:1` — `/projects/start`. **KHÔNG ĐƯỢC ĐỤNG** (production).
- `apps/api/services/credit_manager.py:43` — `CreditManager` class. Phase này chỉ verify import OK sau migration cleanup.
- `apps/api/modules/module_2a/routes.py:1` — `/api/collect/channel`. **CÓ THỂ tham chiếu** cho `/api/channels/collect`.
- `apps/api/modules/transcript/engine.py` — Phase này KHÔNG đụng engine, chỉ tham chiếu cho import type.

### Backend (apps/worker) - CẦN TẠO MỚI
- `apps/worker/tasks/collect_channel_task.py` — **CHƯA TỒN TẠI**, cần tạo mới Celery task gọi `YouTubeCollector` + insert DB.
- `apps/worker/tasks/analysis_task.py` — **CẦN SỬA** để bỏ `fetch_mock_data()`, dùng data từ DB + `TranscriptEngine`.

### Backend (apps/api/routers) - CẦN TẠO MỚI
- `apps/api/routers/assistants.py` — **CHƯA TỒN TẠI**. Cần có: GET /api/assistants, GET /api/assistants/{id}, DELETE /api/assistants/{id}.
- `apps/api/routers/jobs.py` — **CHƯA TỒN TẠI**. Cần có: POST /api/jobs/trigger, GET /api/jobs/{id}, GET /api/jobs/recent.
- `apps/api/routers/analysis.py` — **CHƯA TỒN TẠI**. Cần có: GET /api/analysis/{assistant_id}, POST /api/analysis/{assistant_id}/reanalyze.
- `apps/api/routers/ideas.py` — **CHƯA TỒN TẠI**. Cần có: GET /api/ideas/{assistant_id}.
- `apps/api/routers/channels.py` — **CHƯA TỒN TẠI**. Cần có: POST /api/channels/collect (wrapper gọi `YouTubeCollector` + enqueue task).

### Migrations (supabase/migrations/)
- `0006_credit_hold_commit.sql` — định nghĩa `hold_credits(p_user_id, p_job_id, p_amount)` CŨ + `partial_commit_credits(p_user_id, p_job_id, p_actual_cost)` CŨ + `release_credits(p_user_id, p_job_id)` (dead function).
- `0020_credit_tiers.sql` — định nghĩa `hold_credits(p_user_id, p_amount, p_job_id)` MỚI + `partial_commit_credits(p_job_id, p_final_amount)` MỚI.
- `0011_transcripts_cron.sql` — chỉ tạo table + cron, KHÔNG có policy RLS.
- `0015_rls_policies.sql` + `0019_enable_rls_policies.sql` — chứa policy leaky "Authenticated users can view transcripts".

### Web (apps/web/app/api) - ĐÃ CÓ SẴN, chỉ chờ backend
- `apps/web/app/api/assistants/route.ts` — proxy → `/api/assistants`
- `apps/web/app/api/assistants/[id]/route.ts` — proxy → `/api/assistants/{id}`
- `apps/web/app/api/jobs/[id]/route.ts` — proxy → `/api/jobs/{id}`
- `apps/web/app/api/analysis/[assistant_id]/route.ts` — proxy → `/api/analysis/{id}`
- `apps/web/app/api/ideas/[assistant_id]/route.ts` — proxy → `/api/ideas/{id}`
- **KHÔNG CÓ** proxy cho `/api/jobs/trigger`, `/api/jobs/recent`, `/api/channels/collect`, `/api/credits/pricing` — Phase này tạo mới.

## 4. Dependencies
- **External:** fastapi, supabase-py, celery, redis, pydantic
- **Internal:**
  - `apps.api.dependencies.auth.get_supabase_user`
  - `apps.api.dependencies.supabase.get_supabase_admin`
  - `apps.api.services.credit_manager.CreditManager`
  - `apps.api.modules.module_2a.service.YouTubeCollector`
  - `apps.api.modules.transcript.engine.TranscriptEngine`
  - `apps.worker.celery_app`

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7). Tất cả verify command dùng `Invoke-RestMethod`, `pytest`.
- **Line Ending:** CRLF.
- **Migration order:** Tất cả migrations chạy theo tên file tăng dần (Supabase CLI `supabase db push`). Migration mới phải đánh số > `0022_admin_panel_foundation.sql` (đã viết ở Phase 5) → dùng `0023_preflight_cleanup.sql`.
- **Backward compatibility:**
  - Khi DROP FUNCTION `hold_credits` cũ, **PHẢI DROP theo cả 2 signature** (`(UUID, UUID, INT)` và `(UUID, INT, UUID)` — dù chỉ 1 signature tồn tại, dùng `DROP FUNCTION IF EXISTS` cho cả 2).
  - Web proxy routes **ĐÃ TỒN TẠI** — chỉ cần backend. KHÔNG sửa web proxy.
- **BẢO TỒN:** `apps/api/routers/projects.py`, `apps/api/modules/voice/*`, `apps/worker/tasks/script_generate.py`, `apps/worker/tasks/idea_generate.py`, `apps/worker/tasks/scene_breakdown.py` (đang chạy production).
- **Không có dependency mới** được phép cài (`pip install`).

## 6. Output mong đợi
Sau Phase 1, các trang web `/assistants`, `/jobs/[id]`, `/analysis/[id]`, `/ideas/[id]`, `/projects/new`, `/dashboard`, `/billing` không còn trả về 500. Admin Phase 6+ có data thật để test.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- 7 endpoint FastAPI mới + 4 web proxy mới + migration cleanup + analysis_task refactor.
- Unit test `test_credit_manager.py` vẫn PASSED.
- Smoke test: `/api/assistants` GET trả về 200 (kể cả array rỗng).
- Không có regression trên 12 routers cũ.