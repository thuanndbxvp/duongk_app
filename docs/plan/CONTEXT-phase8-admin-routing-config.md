# Bối cảnh Hệ thống (CONTEXT): phase8-admin-routing-config

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A4)
- **Phase 5 đã xong:** `require_admin` + `audit.py:log_admin_action` + migration 0022.
- **Phase 6 đã viết plan** (chưa thực thi): 3 routers admin (users/credit/pricing).
- **Phase 7 đã viết plan** (chưa thực thi): 3 migration + 3 service (vault/key_resolver/usage_tracker) + 2 routers admin (api_keys/alerts) + 6 web proxy + 2 trang admin.
- **Đây là Sprint A4:** Service Routing Config — phase phức tạp nhất vì **refactor worker + Redis pub/sub**.

## 2. Codebase Analysis (qua Read + Grep)

### 8 nghiệp vụ cần routing (admin_panel_plan.md mục 2.3)
| Feature | Primary | Fallback chain | Hiện trạng |
|---------|---------|----------------|------------|
| `transcript_extract` | supadata | youtube-transcript-api → modal_whisper | Đã có `TranscriptEngine` với 3-tier fallback cứng (engine.py) |
| `llm_text` (script gen) | openai | stali | Đã có `script_generate.py` (worker) gọi OpenAI trực tiếp |
| `embedding` (RAG) | cohere | openai | Đã có `apps/api/modules/rag/embedder.py` |
| `emotion_classifier` | openai | — | Đã có ở `apps/worker/services/antislop_service.py` |
| `ffmpeg_render` | modal_t4 | modal_a10g → local_cpu | **CHƯA CÓ** (plan: `apps/worker/services/render_dispatcher.py`) |
| `tts` | modal_omnivoice | elevenlabs → openai_tts | Đã có `apps/api/modules/voice/routes.py` |
| `thumbnail_vision` | openai | gemini | **CHƯA CÓ** (plan: vision module) |
| `footage_search` | pexels | pixabay → unsplash | Đã có ở `apps/api/modules/module_1/service.py` (Pytrends fallback) |

### Consumer pattern hiện tại (qua Grep)
- **`apps/api/modules/transcript/engine.py:36-37`** — `os.environ.get("SUPADATA_API_KEY")` + `os.environ.get("OPENAI_API_KEY")`.
- **`apps/api/modules/voice/routes.py:16-18`** — `os.environ["R2_*"]` trực tiếp (TTS upload R2).
- **`apps/worker/services/omnivoice_client.py`** — `modal.Function.lookup` (Modal TTS).
- **`apps/worker/tasks/script_generate.py`** — OpenAI client trực tiếp.
- **`apps/api/modules/rag/embedder.py`** — Cohere client trực tiếp.

### Pattern: Tất cả consumer hardcode env var + primary provider
- Phase 8 cần refactor → `service_routing_config` table (DB-driven).
- Cấu trúc routing per feature:
  ```json
  {
    "feature": "transcript_extract",
    "primary_provider": "supadata",
    "fallback_chain": ["youtube_transcript_api", "modal_whisper"],
    "enabled_providers": {"supadata": true, "youtube_transcript_api": true, "modal_whisper": true},
    "cost_per_call_usd": {"supadata": 0.001, "modal_whisper": 0.006}
  }
  ```

### Files KHÔNG tồn tại (cần tạo mới)
- `supabase/migrations/0026_service_routing_config.sql` — table + seed 8 features + trigger `pg_notify`.
- `apps/api/services/cache.py` — Redis client wrapper + `publish(channel, message)` + `subscribe(channel, callback)`.
- `apps/api/services/routing.py` — `get_routing_config(feature)` với cache 60s + Redis invalidate.
- `apps/worker/services/config_watcher.py` — Celery worker subscribe `routing:config:update` channel + polling fallback 60s.
- `apps/api/routers/admin_routing.py` — 5 endpoints (list, get, patch, reload, cost-estimate).
- `apps/web/app/api/admin/routing-config/route.ts` — web proxy.
- `apps/web/app/api/admin/routing-config/[feature]/route.ts` — web proxy.
- `apps/web/app/api/admin/routing-config/[feature]/reload/route.ts` — web proxy.
- `apps/web/app/(admin)/admin/routing/page.tsx` — UI 8 cards.

### Consumer refactor (5 file cần UPDATE)
| File | Refactor scope |
|------|----------------|
| `apps/api/modules/transcript/engine.py` | Thay hardcoded tier → gọi `routing.get_routing_config('transcript_extract')` + iterate fallback_chain |
| `apps/api/modules/voice/routes.py` | TTS provider selection từ `routing.get_routing_config('tts')` |
| `apps/api/modules/rag/embedder.py` | Embedding provider từ `routing.get_routing_config('embedding')` |
| `apps/worker/tasks/script_generate.py` | LLM text từ `routing.get_routing_config('llm_text')` |
| `apps/worker/tasks/analysis_task.py` | Emotion classifier từ `routing.get_routing_config('emotion_classifier')` |

### Files KHÔNG đụng
- Phase 5/6/7 files (admin router đã có).
- Worker task files KHÔNG thuộc routing (collect_channel, idea_generate, scene_breakdown).
- `transcript.routes.py` (chỉ wrapper, không consumer).
- `voice/__init__.py` (chỉ exports).

## 3. Các File liên quan và Vai trò

### Migration (1 NEW)
- `supabase/migrations/0026_service_routing_config.sql` — table `service_routing_config` + seed 8 features + trigger `pg_notify('routing:config:update', ...)`.

### Backend services (3 NEW)
- `apps/api/services/cache.py` — Redis pub/sub wrapper.
- `apps/api/services/routing.py` — DB lookup + 60s cache + Redis invalidate.
- `apps/worker/services/config_watcher.py` — Worker subscribe + fallback polling.

### Backend routers (1 NEW)
- `apps/api/routers/admin_routing.py` — 5 endpoints (list, get, patch, reload, cost-estimate).

### Backend consumer refactor (5 UPDATE)
- 5 file consumer dùng `routing.get_routing_config(feature)` thay hardcode.

### Frontend (3 NEW + 1 UPDATE)
- 3 web proxy routes.
- 1 trang admin `/admin/routing` với 8 cards.
- Sidebar enable Routing.

## 4. Dependencies
- **External:** `redis` (Python) đã có (Celery dùng). `psycopg2` (cho `LISTEN/NOTIFY`) đã có hoặc cần cài.
- **Internal:** `apps.api.services.cache.publish/subscribe`, `apps.api.dependencies.admin.require_admin`, `apps.api.services.audit.log_admin_action`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Backward compatible:** Phase 8 chỉ thêm lớp routing, KHÔNG phá vỡ consumer cũ. Nếu `routing.get_routing_config()` fail → fallback về env var cũ (graceful degradation).
- **Hot-reload:** Admin save UI → publish Redis → worker nhận signal → reload cache. Fallback: worker poll DB mỗi 60s.
- **Audit mask:** Mutation routing PHẢI qua `log_admin_action()`.
- **Cost estimate:** Query `api_usage_logs` 7 ngày gần nhất → avg cost per provider per feature.
- **Worker KHÔNG restart:** Phase 8 verify hot-reload KHÔNG cần restart celery worker.

## 6. Output mong đợi

Sau Phase 8:
- Admin click `/admin/routing` → thấy 8 cards (mỗi feature 1 card).
- Click card → expand dropdown primary + ordered fallback list + toggle enabled + cost preview box.
- Save → publish Redis channel → worker reload cache trong < 1s (hoặc polling 60s fallback).
- Job TTS mới dùng provider admin vừa chọn.
- Cost estimate hiển thị dựa trên `api_usage_logs` 7d.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- Migration 0026 apply thành công (8 features seeded).
- 3 service mới (`cache`, `routing`, `config_watcher`).
- 5 consumer refactor dùng `routing.get_routing_config()`.
- 5 endpoint admin mới.
- 3 web proxy + 1 trang admin + sidebar update.
- Verify hot-reload: admin save routing config → worker không cần restart vẫn pick up config mới trong < 60s.
- TS compile 0 errors.
- Existing pytest PASSED.
- 0 regression trên TTS/Transcript/RAG/Script Generate.