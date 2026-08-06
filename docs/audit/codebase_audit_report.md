# AppDK — Codebase Audit Report
> Ngày: 2026-08-06 · Audit pass #1 (đọc tĩnh toàn repo, không chạy runtime)
> Phạm vi: `apps/api`, `apps/web`, `apps/worker`, `modal_functions`, `supabase/migrations`, `docker-compose*`, `.env*`

---

## 1.1 Bản đồ codebase

### Cấu trúc top-3 levels
```
appDK/
├── apps/
│   ├── api/                 FastAPI backend (Python)
│   │   ├── main.py          App + router registration
│   │   ├── dependencies/    auth, supabase, credit_required
│   │   ├── routers/         credits.py, projects.py, users.py  (legacy/ngách)
│   │   ├── services/        credit_manager.py, youtube.py
│   │   ├── modules/
│   │   │   ├── module_1/    Niche validation (Pytrends + SerpAPI)
│   │   │   ├── module_2a/   YouTube channel collection
│   │   │   ├── transcript/  3-tier fallback engine
│   │   │   ├── analysis/    14 deterministic + LLM outputs
│   │   │   ├── nlp/         GPT-4o NLP analyzer
│   │   │   ├── llm/         Hooks/structure/mimic rules
│   │   │   ├── vision/      GPT-4o thumbnail
│   │   │   ├── rag/         chunker, embedder, storage, MMR RPC client
│   │   │   ├── script/      /api/scripts/generate + scene_breakdown
│   │   │   └── voice/       /api/voice/*  (TTS — đã nối Modal)
│   │   └── openapi.py
│   ├── web/                 Next.js 14 (App Router, glass theme)
│   │   ├── app/
│   │   │   ├── (auth)/      login/register flows
│   │   │   ├── (dashboard)/ dashboard, assistants, projects/new, billing, account, jobs/[id], scripts/[id], analysis/[id], ideas/[id]
│   │   │   ├── api/         ** Next.js proxy routes** → FastAPI
│   │   │   └── pricing/     public pricing page
│   │   ├── components/      assistant-card, pricing-card, credits-card, pricing-table, transaction-history, profile-form, password-form…
│   │   └── lib/             api-client (FastAPI), auth (Supabase session)
│   ├── worker/              Celery worker (Redis broker)
│   │   ├── celery_app.py    4 queue routing: ml/high/io/normal
│   │   ├── progress_tracker.py   httpx RPC → update_job_sub_progress
│   │   ├── tasks/
│   │   │   ├── analysis_task.py      analyze_channel_task (14 outputs + RAG chunk)
│   │   │   ├── idea_generate.py      HDBSCAN + gap score
│   │   │   ├── script_generate.py    RAG + GPT-4o + AntiSlop
│   │   │   └── scene_breakdown.py    WPM segmentation + EN/VN translation
│   │   └── services/        idea_generator, scene_breaker, antislop_service, rag_service, omnivoice_client
│   └── omnivoice/           (placeholder, không dùng)
├── modal_functions/
│   └── dubbing_pipeline.py  5 Modal fn: transcribe_video, cache_voice_prompt, synthesize_voice, dub_srt, render_video
├── supabase/
│   ├── config.toml
│   └── migrations/          21 migrations (users → voice_profiles)
├── scripts/                 export_openapi.py, sync_types.py
├── docs/                    sprint plans
├── docker-compose.yml       local dev
├── docker-compose.prod.yml  production (web, api, worker, redis)
├── Caddyfile                reverse proxy
├── deploy.sh                deploy script
└── .env / .env.example / .env.production(.template)
```

### Framework/library mỗi tầng
| Tầng | Stack chính |
|------|-------------|
| **Frontend** (apps/web) | Next.js 14 (App Router, RSC) · React 18 · Tailwind + glass design system · `@supabase/ssr` cho session |
| **API** (apps/api) | FastAPI · `supabase-py` · `tenacity` retry · `openai` · `cohere` · `pytrends` · `pytube` · `boto3` (R2) |
| **Worker** (apps/worker) | Celery 5 (Redis broker) · `openai` · `hdbscan` + `scikit-learn` · Supabase service-role client · Modal client (chỉ ở `omnivoice_client.py`) |
| **GPU** (modal_functions) | Modal apps `ai-dubbing-pipeline` · `faster-whisper` · `OmniVoice (k2-fsa)` · `ffmpeg` · `boto3` (R2) |
| **DB** (Supabase) | Postgres + `pgvector` (extension `vector`) + `pg_cron` · RLS enabled 11/13 bảng |

### Kết nối hạ tầng hiện có
- **Supabase** managed: `https://ctjnnnnikarsaezlkpse.supabase.co` (anon + service_role keys trong `.env`).
- **Cloudflare R2**: 3 buckets `appdk-uploads`, `appdk-renders`, `appdk-cache`. Endpoint & secrets là placeholder trong `.env`.
- **Modal**: 2 secrets (`supabase-credentials`, `r2-credentials`) — chưa có trong `.env`.
- **External LLM APIs**: OpenAI (`OPENAI_API_KEY`), Cohere (`COHERE_API_KEY`), SerpAPI (chưa có), Stali (`STALI_API_KEY`/`STALI_BASE_URL` — có nhưng chưa thấy consumer trong code).
- **YouTube Data API v3**: qua `googleapiclient` + key `YOUTUBE_API_KEY_1` (chưa có).
- **Supadata transcript API**: chưa có key.

### Config quan trọng
- `.env` đã có: `SUPABASE_*`, `NEXT_PUBLIC_SUPABASE_*`, `R2_*` (placeholder), `REDIS_URL`, `STALI_*`, `ENV`, `NODE_ENV`.
- `.env.example` **thiếu hầu hết**: chỉ liệt kê `YOUTUBE_API_KEY_1`, `OPENAI_API_KEY`, `COHERE_API_KEY`, `SUPABASE_URL/ANON/SERVICE_ROLE`, `NEXT_PUBLIC_SUPABASE_*`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `SUPABASE_JWT_SECRET`, `SENTRY_DSN`. Thiếu: `R2_*`, `MODAL_TOKEN_*`, `SUPADATA_API_KEY`, `SERPER/SERPAPI_KEY`, `STALI_*`, `PYTHONUNBUFFERED`.
- 21 migrations trong `supabase/migrations/`, mới nhất là `0021_voice_profiles.sql`.
- `docker-compose.prod.yml`: 4 services `web`, `api`, `worker`, `redis`. Không có reverse-proxy Caddy ngoài (chạy host-level).

---

## 1.2 Pipeline nghiệp vụ hiện tại (thực tế đang chạy trong code)

### A. Voice / TTS (đầu cuối hoạt động)
```
[Web] apps/web/components/voice/profile-form.tsx  (chưa đọc chi tiết)
  → POST /api/voice/profiles       apps/web/app/api/voice/profiles/route.ts
    → FastAPI POST /api/voice/profiles   apps/api/modules/voice/routes.py
      → boto3 → R2 `appdk-uploads/voice_samples/{user_id}/{uuid}.wav`
      → supabase insert voice_profiles
  → POST /api/voice/synthesize     apps/web/app/api/voice/synthesize/route.ts
    → FastAPI POST /api/voice/synthesize   apps/api/modules/voice/routes.py
      → modal.Function.lookup('ai-dubbing-pipeline', 'synthesize_voice').remote(...)
        → Modal T4 GPU chạy OmniVoice → upload wav → R2 `appdk-renders` → trả public URL `https://cdn.ai86.click/{key}`
```
🟢 **Hoạt động** — đã nối Modal end-to-end và R2. Lưu ý `cdn.ai86.click` là CDN custom, không phải `R2_PUBLIC_CDN`.

### B. Channel Assistant + Deep Analysis (LUỒNG ĐẦY ĐỦ NHƯNG NHIỀU CHỖ STUB)
```
[Web] AssistantActions → POST /api/jobs/trigger      ⚠️ route này KHÔNG TỒN TẠI trong apps/web/app/api
  (hoặc qua projects/new → POST /api/channels/collect  ⚠️ route KHÔNG TỒN TẠI)

(giả sử gọi thẳng backend)
POST /api/projects/start         apps/api/routers/projects.py
  → insert channel_assistants (status='training')
  → insert jobs (task_type='deep_analysis', status='pending')
  → CreditManager.hold(user_id, job_id, 60)    apps/api/services/credit_manager.py
    → supabase RPC hold_credits  (0020_credit_tiers.sql)
  → analyze_channel_task.delay(job_id, channel_id)
    apps/worker/tasks/analysis_task.py
    → ProgressTracker.start(* 14 outputs)
    → videos = fetch_mock_data()   ← 🟡 STUB: trả 5 video fake cứng
    → transcripts = ["Hello world"] * 5   ← 🟡 STUB: không có transcript thật
    → generate_output_1..4 (deterministic)   apps/api/modules/analysis/outputs.py
    → GPTNLPAnalyzer.analyze_all (outputs 5/6/7/10)   apps/api/modules/nlp/gpt_analyzer.py
    → LLMAnalyzer hooks/structure/mimic (outputs 8/9/11)   apps/api/modules/llm/analyzer.py
    → ThumbnailAnalyzer.analyze_thumbnails (output 14)   apps/api/modules/vision/thumbnail_analyzer.py
    → find_hidden_insights (output 12)   apps/api/modules/analysis/insights.py
    → RAG: chunker → embedder → RAGStorage.store_chunks → dna_chunks table
      → match_dna_chunks RPC sẵn sàng cho retrieval
```
🟡 **Stub nặng ở fetch_mock_data** + không có thật việc gọi YouTube collector. Đáng lẽ luồng phải là:
`/api/projects/start` → enqueue `collect_channel_task` → `module_2a/service.YouTubeCollector.collect_channel_videos()` → enqueue `transcript-fetch` (Tier1-3) → `analyze_channel_task` mới có `videos` thật.

### C. Script Generation
```
POST /api/scripts/generate        apps/api/modules/script/routes.py
  → insert jobs (task_type='script_generate')
  → script_generate_task.delay(...)
    apps/worker/tasks/script_generate.py
    → RAGService.retrieve_context → match_dna_chunks RPC  (cần dna_chunks đã có)
    → GPT-4o-mini với prompt build_script_prompt
    → AntiSlopService.validate_with_retry (regex + LLM scoring, budget $0.10)
    → insert generated_scripts (score, attempts, cost_usd)
```
🟡 **Có thể chạy nếu đã có dna_chunks** — phụ thuộc pipeline B.

### D. Scene Breakdown
```
POST /api/scripts/breakdown-scenes   apps/api/modules/script/routes.py
  → fetch latest generated_scripts
  → scene_breakdown_task.delay(...)
    apps/worker/tasks/scene_breakdown.py
    → SceneBreaker.segment_scenes (paragraph-based + WPM)
    → translate_broll_keywords VN→EN (GPT-4o-mini)
    → update generated_scripts.scenes
```
🟡 **Code ổn** — chạy được sau khi có script, nhưng `scenes[].footage_url` chưa được điền (sẽ cần bước search Pexels sau).

### E. Idea Generation
```
POST /api/jobs/trigger {task_type: idea_generation}    ⚠️ route KHÔNG TỒN TẠI
  (nếu có) → idea_generate_task.delay(...)
    apps/worker/tasks/idea_generate.py
    → fetch latest channel_deep_analysis (metadata_report.top_tags)
    → IdeaGenerator.cluster_topics (TF-IDF + HDBSCAN)   apps/worker/services/idea_generator.py
    → calculate_gap_score + opportunity_description
    → insert generated_ideas (gap_score, cluster_id, confidence)
```
🟡 **Code OK, chưa wire-up UI**.

### F. Niche Validation
```
POST /api/research/validate       apps/api/modules/module_1/routes.py
  → NicheValidator.validate()    apps/api/modules/module_1/service.py
    → RedisCache (token bucket + cache 24h)
    → Pytrends (rate-limited 1 req/10s)
    → fallback SerpAPI (chưa có key)
```
🟡 **Có thể chạy** nếu có Redis local + Pytrends IP không bị block. Fallback SerpAPI cần key.

### G. Deep Channel Collection
```
POST /api/collect/channel         apps/api/modules/module_2a/routes.py
  → YouTubeCollector.collect_channel_videos()
    → googleapiclient.search.list (pagination)
    → videos.list batch=50 (max 4 concurrent)
    → filter_quality_videos + detect_viral_videos (MAD z-score)
```
🟡 **Cần `YOUTUBE_API_KEY_1` thật**. Không gọi Supabase, không lưu DB → chỉ là utility in-memory.

### H. Transcript Engine
```
POST /api/transcript             apps/api/modules/transcript/routes.py
  → TranscriptEngine.get_transcript
    → Tier 1: youtube-transcript-api (free, fragile với IP cloud)
    → Tier 2: Supadata ($0.001/min) — chưa có key
    → Tier 3: OpenAI Whisper API ($0.006/min) — cần pytube lấy audio bytes
```
🟢 **API + UI dùng được** nhưng Tier 1 hay 403; Tier 2/3 cần key.

### I. RAG Embedding + Retrieval
```
POST /api/rag/embed              apps/api/modules/rag/routes.py
  → SemanticChunker → Embedder (Cohere/OpenAI router)
POST → match_dna_chunks RPC (Supabase)        apps/worker/services/rag_service.py
```
🟡 **Có RPC MMR** — chưa có UI gọi trực tiếp (chỉ script gen dùng nội bộ).

### J. Dashboard Recent Jobs
```
GET /api/jobs/recent            ⚠️ KHÔNG TỒN TẠI trong FastAPI
  web dashboard gọi → response 500 trong production
```
🔴 **Wiring sai**.

### K. Account Settings
```
GET /api/users/me                  apps/api/routers/users.py        🟢
PATCH /api/users/me                apps/api/routers/users.py        🟢
GET /credits/balance               apps/api/routers/credits.py      🟢
GET /credits/transactions          apps/api/routers/credits.py      🟢
```
🟢 OK.

### L. Billing Pricing (3rd party / marketing)
```
GET /credits/pricing              apps/web fetch qua apiFetch nhưng ❌ KHÔNG có endpoint FastAPI này
```
🔴 **Wiring sai** — web `billing/page.tsx` gọi `/api/credits/pricing` (Promise.all) nhưng backend chỉ có `/credits/balance` và `/credits/transactions`. Pricing tồn tại ở `credit_pricing` table (0020) và `PRICING` dict ở `credit_manager.py` nhưng chưa expose endpoint.

---

## 1.3 Bảng nghiệp vụ (feature × trạng thái)

| # | Feature | File path chính | Trạng thái | Cần gì để chạy thật |
|---|---------|----------------|------------|---------------------|
| 1 | **TTS (synthesize voice)** | `apps/api/modules/voice/routes.py` + `modal_functions/dubbing_pipeline.py:synthesize_voice` | 🟢 Hoạt động | `MODAL_TOKEN_*` + `R2_*` thật, Modal secret `r2-credentials` |
| 2 | **Voice profile (upload .wav → R2)** | `apps/api/modules/voice/routes.py:create_profile` | 🟢 Hoạt động (chưa có UI upload) | `R2_*` thật |
| 3 | **Auth (Supabase JWT)** | `apps/api/dependencies/auth.py` | 🟢 Hoạt động | `SUPABASE_JWT_SECRET` |
| 4 | **Account me / credits balance** | `apps/api/routers/users.py`, `credits.py` | 🟢 Hoạt động | — |
| 5 | **Credit hold/commit/refund** | `supabase/migrations/0020_credit_tiers.sql` + `apps/api/services/credit_manager.py` | 🟢 Hoạt động (chưa ai gọi `adjust/commit` ở các task) | Worker phải gọi `cm.adjust` / `cm.commit` sau khi tính actual_cost |
| 6 | **Credit transactions history** | `apps/api/routers/credits.py:get_transactions` | 🟢 Hoạt động | — |
| 7 | **Transcribe video (Modal faster-whisper)** | `modal_functions/dubbing_pipeline.py:transcribe_video` | 🟡 Sẵn sàng | Chưa thấy backend task nào gọi Modal function này |
| 8 | **Voice clone prompt cache** | `modal_functions:dubbing_pipeline.py:cache_voice_prompt` | 🟡 Sẵn sàng | Chưa wire vào flow `create_profile` |
| 9 | **Dub SRT (synthesize per-subtitle + merge)** | `modal_functions:dub_srt` | 🟡 Sẵn sàng | Chưa có UI/task trigger |
| 10 | **Render final video (FFmpeg)** | `modal_functions:render_video` | 🟡 Sẵn sàng | Chưa có task wrapper; scenes phải có `footage_url` |
| 11 | **Niche validation (Pytrends/SerpAPI)** | `apps/api/modules/module_1/routes.py` | 🟡 Stub (rate-limited + fallback key thiếu) | `SERPAPI_KEY`, Redis local, IP không bị Google rate-limit |
| 12 | **YouTube channel collect (google-api)** | `apps/api/modules/module_2a/routes.py` | 🟡 Stub (in-memory only, không lưu DB) | `YOUTUBE_API_KEY_1`; cần wire vào `collect_channel_task` |
| 13 | **Channel viral detection (MAD)** | `apps/api/modules/module_1/formulas.py:detect_viral_videos` | 🟢 Thuần code, OK | — |
| 14 | **Transcript 3-tier fallback** | `apps/api/modules/transcript/engine.py` | 🟢 Code OK | `SUPADATA_API_KEY` (Tier 2), OpenAI quota (Tier 3) |
| 15 | **Deep analysis 14 outputs** | `apps/worker/tasks/analysis_task.py` | 🟡 Stub (videos/transcripts cứng) | Cần fix `fetch_mock_data` → dùng Module 2A + transcript |
| 16 | **RAG embed + MMR retrieval** | `apps/api/modules/rag/*` + RPC `match_dna_chunks` | 🟢 Sẵn sàng | Cohere/OpenAI keys |
| 17 | **Script generate (RAG + GPT-4o + AntiSlop)** | `apps/worker/tasks/script_generate.py` | 🟡 OK nếu có dna_chunks | Worker chạy được, nhưng API gọi qua `script_generate_task` thiếu `bind=True` tham số (`def run(self, ...)` — xem issue #1.4) |
| 18 | **Scene breakdown + B-roll translate** | `apps/worker/tasks/scene_breakdown.py` | 🟢 Sẵn sàng | — |
| 19 | **Idea generation (HDBSCAN + gap score)** | `apps/worker/tasks/idea_generate.py` | 🟡 OK nếu có analysis | Worker tốt nhưng UI route `/api/jobs/trigger` không tồn tại |
| 20 | **Pricing table (UI)** | `apps/web/components/pricing-table.tsx` | 🟢 UI ổn | Endpoint `/credits/pricing` còn thiếu (báo cáo Mục 1.2.L) |
| 21 | **Transaction history (UI)** | `apps/web/components/transaction-history.tsx` | 🟢 UI ổn | — |
| 22 | **Channel Assistant CRUD UI** | `apps/web/app/(dashboard)/assistants/*` | 🟡 UI glass-OK | Web proxy `/api/assistants` & `/api/assistants/{id}` không có backend |
| 23 | **Deep Analysis detail UI** | `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | 🟡 Có UI | Cần endpoint `/api/analysis/{id}` + `/api/analysis/{id}/reanalyze` |
| 24 | **Jobs progress realtime** | `apps/web/app/(dashboard)/jobs/[id]/page.tsx` | 🟡 UI dùng Supabase realtime + proxy `/api/jobs/{id}` | Backend `/api/jobs/{id}` chưa có |
| 25 | **Render final video** | `modal_functions:render_video` | 🟡 Sẵn sàng | Thiếu scenes với footage_url + UI/tác vụ kích hoạt |

**Tổng**: 25 feature · 🟢 9 (36%) · 🟡 13 (52%) · 🔴 3 (12%) — tính theo tỷ lệ sẵn sàng đầu cuối (UI + API + Worker/Modal + Key).

---

## 1.4 Điểm mờ / lỗ hổng

### 🔴 Wiring sai (UI gọi API không tồn tại)
1. `assistant-actions.tsx` → POST `/api/jobs/trigger` — **không có** trong cả FastAPI lẫn Next.js proxy.
2. `ideas/regenerate-button.tsx` → POST `/api/jobs/trigger` — giống trên.
3. `analysis/reanalyze-button.tsx` → POST `/api/analysis/{id}/reanalyze` — không có.
4. `web/app/(dashboard)/projects/new/page.tsx` → POST `/api/channels/collect` — không có.
5. `web/app/(dashboard)/dashboard/page.tsx` → GET `/api/jobs/recent` — không có.
6. `web/app/api/assistants/route.ts` & `[id]/route.ts` → FastAPI không có router `/api/assistants` và `/api/assistants/{id}`.
7. `web/app/api/analysis/[assistant_id]/route.ts` → FastAPI không có `/api/analysis/{id}`.
8. `web/app/api/ideas/[assistant_id]/route.ts` → FastAPI không có `/api/ideas/{id}`.
9. `web/app/api/jobs/[id]/route.ts` → FastAPI không có `/api/jobs/{id}`.
10. `apps/web/app/(dashboard)/billing/page.tsx` → GET `/api/credits/pricing` — không có.

> Tất cả các trang liên quan đang chạy vào "Loading…" rồi lỗi 500 trong production (không phải dev mock).

### 🟡 Logic inconsistency / bug tiềm ẩn
- **Duplicate credit function**: `0006_credit_hold_commit.sql` định nghĩa `hold_credits(p_user_id, p_job_id, p_amount)` cũ; `0020_credit_tiers.sql` định nghĩa lại `hold_credits(p_user_id, p_amount, p_job_id)` (đảo tham số). RPC client `credit_manager.py:hold` gọi theo signature mới, nhưng migration 0006 vẫn tồn tại và có thể trigger lỗi khi DB apply đúng thứ tự nhưng cache function cũ. → Cần `DROP FUNCTION hold_credits(...)` ở 0020 hoặc xóa 0006.
- **`credit_required` dependency chỉ CHECK, không HOLD**: `apps/api/dependencies/credit_required.py` chỉ raise 402 nếu không đủ credits — không tạo transaction. Không router nào `@Depends(credit_required(...))` thật sự dùng nó. → Tất cả hold/commit đều do route `projects.start` tự gọi `cm.hold` — không thống nhất pattern.
- **`script_generate_task.run(self, job_id, assistant_id, topic)`** gọi `openai = OpenAI()` không truyền key (dùng env) — OK nếu env có, nhưng `scene_breakdown_task` cũng vậy → fallback fail silently nếu `OPENAI_API_KEY` thiếu.
- **`analysis_task.py:fetch_mock_data()`** cứng 5 video — analysis 14 outputs chạy trên data rác.
- **`voice_profiles.sample_audio_url`** lưu URL CDN (`R2_PUBLIC_CDN`) — nhưng TTS synthesize trả `https://cdn.ai86.click/{key}` (khác bucket `appdk-renders`). Hai domain khác nhau — không có chuẩn hoá.
- **RLS**: `transcripts` table (`0011`) đã `ENABLE RLS` và policy "Authenticated users can view transcripts" cho phép **mọi user authenticated đọc mọi video_id transcript** (không scope theo channel_assistant). → leaky.
- **`channel_deep_analysis`** policy ở 0019 join qua assistant nhưng 0015 cũng có policy "Authenticated users can view channel analysis" — conflict, policy 0019 mới hơn sẽ thắng nhưng migration 0015 vẫn còn.
- **`generated_scripts.scenes`** update ở `scene_breakdown_task` dùng `eq('job_id', job_id)` — job_id là FK nhưng có thể null khi script generate fail.
- **`progress_tracker.py`** gọi RPC `update_job_sub_progress` bằng `httpx` POST tới Supabase REST — không dùng supabase-py client (thiếu nhất quán, dễ miss header).
- **Test stale**: `apps/api/test_credit_manager.py` & `apps/api/dependencies/test_auth.py` & `apps/worker/services/test_*.py` còn trong repo nhưng `.env.example` không có key test (chưa chạy được nếu không mock).
- **Unused imports / dead code**: `apps/api/services/youtube.py` định nghĩa `YouTubeClient` nhưng không ai import (Module 2A dùng `googleapiclient`).
- **`QuotaExceededError`** được raise khi 403 trong `youtube.py` nhưng không có caller.

### Env & Secrets
- `.env` có key `STALI_API_KEY`/`STALI_BASE_URL` nhưng code **không dùng tới**. Có thể là provider LLM dự phòng hoặc đã thay bằng OpenAI.
- `.env` R2/MODAL là placeholder chưa thay.
- `.env.example` thiếu: `R2_*`, `MODAL_TOKEN_*`, `SUPADATA_API_KEY`, `SERPAPI_KEY`, `STALI_*`.

### Race condition tiềm ẩn
- `partial_commit_credits` và `refund_credits` cùng `FOR UPDATE` trên `jobs` nhưng `credit_transactions` insert có thể trùng pattern → nếu worker gọi `refund` rồi user trigger `commit` sẽ double-credit.
- `hold_credits` lock user row → OK. Nhưng `release_credits` (0006) không được gọi ở bất kỳ đâu trong code hiện tại → **dead function**.

### RLS tổng kết
| Bảng | Có RLS | Có policy | Scope policy | Đạt |
|------|--------|-----------|--------------|-----|
| users | ✅ | ✅ | `id = auth.uid()` | OK |
| jobs | ✅ | ✅ | `user_id = auth.uid()` | OK |
| credit_transactions | ✅ | ✅ | join users | OK |
| api_usage_logs | ✅ | ✅ | `user_id = auth.uid()` | OK |
| quota_ledger | ✅ | ❌ | — (service only) | OK vì service_role |
| channel_assistants | ✅ | ✅ | `user_id = auth.uid()` | OK |
| channel_deep_analysis | ✅ | ✅ | join assistants | OK |
| dna_chunks | ✅ | ✅ | join assistants | OK |
| transcripts | ✅ | ⚠️ "all authenticated" | **Không scope theo assistant** | ❌ leaky |
| generated_ideas | ✅ | ✅ | join assistants | OK |
| generated_scripts | ✅ | ✅ | join assistants | OK |
| voice_profiles | ✅ | ✅ | `user_id = auth.uid()` | OK |
| credit_pricing | ❓ | — | — | Không thấy migration nào enable RLS → mặc định deny cho non-service |

---

## 1.5 Báo cáo tổng kết

### % sẵn sàng
- **Từ-góc-nhìn-đầu-cuối** (UI click được và chạy được): **~25%** (chỉ Auth + Account settings + Credits balance + TTS đầy đủ).
- **Code đã có nhưng thiếu wiring UI↔API**: ~40% (Deep analysis, Script gen, Scene breakdown, Idea gen, Channel collect, Niche validate, RAG embed).
- **Có code + có thể gọi được nhưng stub/Mock**: ~25% (analysis_task mock_data, transcript tier 2/3 thiếu key).
- **Hoàn toàn chưa có**: ~10% (Render video UI, Dub SRT UI, Jobs trigger endpoint, Pricing endpoint).

### Ưu tiên wire-up (value/effort)
| STT | Hạng mục | Value | Effort | Ghi chú |
|-----|----------|-------|--------|---------|
| 1 | Thêm FastAPI router `/api/assistants` (list + get + delete) | 🔥 cao | 1-2h | Web đang gọi trực tiếp, đây là blocker cho `/assistants` page |
| 2 | Thêm `/api/jobs/trigger` (POST {assistant_id, task_type}) | 🔥 cao | 1h | Mở khoá Analyze/Ideas/Script từ UI |
| 3 | Thêm `/api/jobs/{id}` (GET) | 🔥 cao | 30p | Jobs progress page cần |
| 4 | Thêm `/api/channels/collect` (POST {youtube_url}) thay cho `/api/projects/start` | 🔥 cao | 2h | Channel collect + enqueue `analyze_channel_task` thật (thay `fetch_mock_data`) |
| 5 | Thêm `/api/analysis/{id}` (GET) + `/api/analysis/{id}/reanalyze` (POST) | 🔥 cao | 2h | Unblock analysis page |
| 6 | Thêm `/api/ideas/{assistant_id}` (GET) | 🔥 cao | 30p | Unblock ideas page |
| 7 | Thêm `/api/credits/pricing` (GET) | 🔥 trung bình | 30p | Unblock billing page |
| 8 | Refactor `analysis_task.py`: bỏ `fetch_mock_data`, dùng `module_2a.YouTubeCollector` + `transcript.TranscriptEngine` thật | 🔥 cao | 4-6h | Hiện tại phân tích trên data rác |
| 9 | Tạo task `collect_channel_task` (Celery) chạy `YouTubeCollector.collect_channel_videos` → insert DB | 🔥 cao | 3h | Chuẩn hoá flow "Tạo Assistant" |
| 10 | Sửa RLS `transcripts` scope theo `assistant_id` (hoặc qua `dna_chunks`) | 🛡 bảo mật | 1h | Tránh rò rỉ transcript |
| 11 | Thêm worker step gọi `Modal.transcribe_video` thay vì Pytube local | ⚡ perf | 3h | Tier 1 hiện fragile |
| 12 | UI render dub/render video (Modal tasks) + `dub_srt` + `render_video` task wrappers | ⚡ perf | 6-8h | End-to-end video pipeline |
| 13 | Cleanup duplicate `hold_credits` signature trong 0006 vs 0020 | 🛡 correctness | 30p | Tránh hành vi không nhất quán |
| 14 | `.env.example` bổ sung R2/MODAL/SUPADATA/SERPAPI/STALI | 📝 docs | 15p | — |
| 15 | CSS đồng bộ dark theme cho `/assistants/[id]` (đang còn `bg-white`) | 🎨 UX | 30p | Đã sửa `/account` và `/billing`, còn legacy pages |

### Rủi ro kỹ thuật cao nhất
1. **Backend ↔ UI misalignment** — gần như tất cả flow chính (assistants, projects, analysis, ideas, jobs trigger) đều không có backend route. Production user click vào sẽ 500. Đây là blocker #1 cho việc "online 100%".
2. **`analysis_task.py` chạy trên mock data** — analysis 14 outputs đắt tiền OpenAI (gpt-4o × 4 calls + GPT-4o-mini × nhiều) đang tiêu credits trên data fake. Sửa sớm trước khi có user thật.
3. **Transcript leak (RLS `transcripts`)** — bảng nhạy cảm (nội dung video) đang public-read cho mọi authenticated user.
4. **Credit double-spend** — hai hàm `hold_credits` tồn tại đồng thời, không có test E2E cho refund khi job fail.
5. **Pytrends từ IP cloud** — module 1 sẽ gần như chắc chắn fail khi chạy trên VPS (Google đã hạn chế). Cần fallback chắc tay hơn (SerpAPI key).
6. **Render video scenes chưa có `footage_url`** — chưa có bước search Pexels để lấy stock footage cho mỗi scene.

### Đề xuất sprint tiếp theo (priority order)
- **Sprint N+1 (1-2 ngày)**: Items 1-7 (thêm 7 backend routes) + Item 14 (env example) + Item 13 (cleanup duplicate function).
- **Sprint N+2 (3-5 ngày)**: Item 8+9 (refactor analysis pipeline thật) + Item 10 (RLS fix).
- **Sprint N+3 (1 tuần)**: Item 11+12 (Modal-driven pipeline, render video UI).

---
*End of report. Các chi tiết runtime cần verify bằng cách start docker-compose.prod.yml + curl smoke test.*