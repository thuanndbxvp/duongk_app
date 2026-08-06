# Tiêu chí Nghiệm thu (ACCEPTANCE): phase8-admin-routing-config

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `supabase/migrations/0026_service_routing_config.sql` (NEW)
- [ ] Có bảng `service_routing_config` với columns: `id`, `feature`, `primary_provider`, `fallback_chain TEXT[]`, `enabled_providers JSONB`, `cost_per_call_usd JSONB`, `config_version`, `updated_by`, `updated_at`, `created_at`.
- [ ] Có index `idx_routing_feature`.
- [ ] Có seed 8 features: `transcript_extract`, `llm_text`, `embedding`, `emotion_classifier`, `ffmpeg_render`, `tts`, `thumbnail_vision`, `footage_search`.
- [ ] Có trigger `trigger_routing_update` (AFTER UPDATE) gọi `pg_notify('routing:config:update', NEW.feature)`.
- [ ] RLS enabled.

### File 2: `apps/api/services/cache.py` (NEW)
- [ ] Có hàm `get_client()` (lazy singleton).
- [ ] Có hàm `publish(channel, message) → int` (số subscriber).
- [ ] Có hàm `subscribe(channel, callback) → Thread` (daemon thread).
- [ ] Có hàm `cache_get(key) → Any` + `cache_set(key, value, ttl)` + `cache_delete(key)`.
- [ ] Auto-serialize JSON cho non-string values.

### File 3: `apps/api/services/routing.py` (NEW)
- [ ] Có hàm `get_routing_config(feature, use_cache=True) → dict`.
- [ ] Cache 60s in-memory (thread-safe).
- [ ] Cache invalidation qua `invalidate_cache(feature)`.
- [ ] Có hàm `get_all_routing_configs()` (list 8 features).
- [ ] Có hàm `get_cost_estimate(feature, window_days=7) → dict[provider, stats]`.
- [ ] Graceful degradation: nếu DB fail → return DEFAULT_CONFIG.

### File 4: `apps/worker/services/config_watcher.py` (NEW)
- [ ] Có hàm `start_watcher()` (idempotent).
- [ ] Subscribe Redis channel `routing:config:update` qua callback `_on_routing_update`.
- [ ] Polling fallback thread (daemon) loop 60s.
- [ ] Detect version mismatch → invalidate cache.
- [ ] KHÔNG tự boot từ celery_app (Phase 8 chỉ cung cấp hàm).

### File 5-9: Consumer refactor (5 UPDATE)
- [ ] `apps/api/modules/transcript/engine.py`: thêm helper `get_routing_config('transcript_extract')` trong `get_transcript()`. Có `_legacy_get_transcript()` fallback.
- [ ] `apps/api/modules/voice/routes.py`: thêm `select_tts_provider()` helper.
- [ ] `apps/api/modules/rag/embedder.py`: thêm `_select_embedding_provider()` helper.
- [ ] `apps/worker/tasks/script_generate.py`: thêm `select_llm_provider()` helper.
- [ ] `apps/worker/tasks/analysis_task.py`: thêm `select_emotion_provider()` helper.
- [ ] Tất cả helper fallback về env var cũ nếu routing rỗng.

### File 10: `apps/api/routers/admin_routing.py` (NEW)
- [ ] Có 5 endpoints:
  - `GET /api/admin/routing-config` (list 8 features + cost estimate 7d)
  - `GET /api/admin/routing-config/{feature}` (1 feature + cost estimate)
  - `PATCH /api/admin/routing-config/{feature}` (update + optimistic locking + publish Redis + audit)
  - `POST /api/admin/routing-config/{feature}/reload` (invalidate cache + publish Redis)
  - `GET /api/admin/routing-config/{feature}/cost-estimate` (window_days query)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Mọi mutation gọi `log_admin_action()`.
- [ ] Optimistic locking: PATCH 409 nếu `expected_version` lệch.

### File 11: `apps/api/main.py` (UPDATE)
- [ ] Có import mới: `admin_routing_router`.
- [ ] Có `app.include_router(admin_routing_router)`.
- [ ] Routing admin route count ≥ 7.

### File 12-14: Web proxy routes (3 NEW)
- [ ] `apps/web/app/api/admin/routing-config/route.ts` (GET).
- [ ] `apps/web/app/api/admin/routing-config/[feature]/route.ts` (GET + PATCH).
- [ ] `apps/web/app/api/admin/routing-config/[feature]/reload/route.ts` (POST).
- [ ] TS compile 0 errors.

### File 15: `apps/web/app/(admin)/admin/routing/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Grid 2 cols, mỗi feature 1 card.
- [ ] Card có dropdown primary + ordered fallback list (với ↑↓ reorder) + toggle enabled + cost preview box + Save + Reload button.
- [ ] Save hiển thị message "worker sẽ reload trong < 60s".

### File 16: `apps/web/app/(admin)/layout.tsx` (UPDATE)
- [ ] `Routing.enabled = true` (line 13).
- [ ] 7 mục còn lại KHÔNG đổi.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Hot-reload:**
  - Admin save UI → worker nhận signal trong < 1s (qua Redis pub/sub) hoặc < 60s (polling fallback).
  - Worker KHÔNG cần restart.
- **Backward compatibility:**
  - 0 regression trên TTS route (test với `MODAL_TOKEN_ID` env).
  - 0 regression trên Transcript (test với `SUPADATA_API_KEY` env).
  - 0 regression trên RAG (test với `COHERE_API_KEY` env).
  - 0 regression trên Script Generate (test với `OPENAI_API_KEY` env).
- **Graceful degradation:**
  - Nếu DB fail → fallback env var cũ (test bằng cách tạm disable DB connection).
  - Nếu Redis fail → polling fallback vẫn hoạt động (max 60s stale).
- **No new dependency:**
  - `redis` (Python) đã có (Celery dùng).
  - `psycopg2` đã có.
- **Multi-process safe:**
  - Mỗi worker process có watcher riêng.
  - Redis pub/sub đảm bảo tất cả worker đồng bộ.

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 8 KHÔNG thêm unit test mới. Verify qua:
  - Smoke test import (10 file).
  - Existing pytest PASSED.
  - Hot-reload manual test (start Redis + worker + admin PATCH → worker logs).

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify Python imports (10 file)
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.cache import get_client, publish, subscribe; print('cache OK')"
python -c "from apps.api.services.routing import get_routing_config; print('routing OK')"
python -c "from apps.worker.services.config_watcher import start_watcher; print('config_watcher OK')"
python -c "from apps.api.routers.admin_routing import router; print('admin_routing OK')"
python -c "from apps.api.modules.transcript.engine import TranscriptEngine; print('engine OK')"
python -c "from apps.api.modules.voice.routes import select_tts_provider; print('voice OK')"
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder OK')"
python -c "from apps.worker.tasks.script_generate import select_llm_provider; print('script_generate OK')"
python -c "from apps.worker.tasks.analysis_task import select_emotion_provider; print('analysis_task OK')"
```
**Expected:** 10 dòng "OK".

### Bước 2: Verify routing config có 8 features
```powershell
python -c "from apps.api.services.routing import get_all_routing_configs; print(len(get_all_routing_configs()), 'features')"
```
**Expected:** `8 features`.

### Bước 3: Verify admin routing routes
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'routing' in r.path]); print(len(routes), 'routing routes')"
```
**Expected:** ≥ 7 routes.

### Bước 4: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 5: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 6: Verify UI page exists
```powershell
Test-Path "app\(admin)\admin\routing\page.tsx"
```
**Expected:** True.

### Bước 7: Verify sidebar update
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "Routing.*enabled.*true"
```
**Expected:** 1 match.

### Bước 8: Hot-reload manual test (cần Redis + worker)
```powershell
# Terminal 1: Start Redis
docker run -p 6379:6379 redis

# Terminal 2: Start worker (verify watcher boot)
cd d:\appDK\apps\worker
celery -A celery_app worker --loglevel=info

# Worker logs sẽ hiển thị:
# [config_watcher] Subscribed to routing:config:update
# [config_watcher] Polling fallback thread started (60s interval)

# Terminal 3: Trigger reload qua API
curl -X PATCH http://localhost:8000/api/admin/routing-config/tts \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"primary_provider": "elevenlabs"}'

# Worker logs sẽ hiển thị:
# [config_watcher] Routing config updated for feature: tts
```
**Expected:** Worker nhận signal trong < 1s.

### Bước 9: Visual smoke test (optional, cần admin role)
```powershell
pnpm dev
```
Mở browser với admin user:
- `/admin/routing` → 8 cards.
- Click card "TTS" → dropdown primary + ordered fallback list + toggle + cost preview.
- Đổi primary từ `modal_omnivoice` → `elevenlabs` → click Save → message "worker sẽ reload trong < 60s".
- Reload page → primary đã đổi.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 15 MSEW step phải PASS verify command của riêng nó, VÀ 9 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase8-admin-routing-config.md` và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Sprint A5 - Polish)
- **Audit log viewer UI** (`/admin/audit-logs`) — Phase 9.
- **2FA bắt buộc cho super_admin** — Phase 9.
- **IP whitelist enforcement** — Phase 9.
- **Backup/restore config** — Phase 9.
- **Documentation handbook** (`docs/admin_handbook.md`) — Phase 9.
- **ffmpeg_render dispatcher** (`apps/worker/services/render_dispatcher.py`) — Phase 9.
- **thumbnail_vision consumer** — Phase 9.