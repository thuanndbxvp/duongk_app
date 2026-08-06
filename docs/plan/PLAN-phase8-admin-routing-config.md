# Kế hoạch Triển khai (PLAN): phase8-admin-routing-config

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Sprint A4 — Service Routing Config cho Admin Panel. Hot-reload 8 nghiệp vụ qua Redis pub/sub, không cần restart worker.
- **Giá trị cốt lõi:**
  1. Admin đổi primary provider cho TTS từ `modal_omnivoice` → `elevenlabs` qua UI — không cần SSH/deploy.
  2. Worker pick up config mới trong < 1s (qua Redis pub/sub) hoặc 60s (fallback polling).
  3. Cost estimate preview dựa trên `api_usage_logs` 7 ngày.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: DB-driven routing + Redis hot-reload
```
[Admin UI] 
  → PATCH /api/admin/routing-config/transcript_extract
    → FastAPI updates service_routing_config table
    → Postgres trigger pg_notify('routing:config:update', 'transcript_extract')
    → Worker config_watcher receives notification
    → Worker invalidates routing cache for that feature
    → Next consumer call: routing.get_routing_config('transcript_extract') reloads from DB

FALLBACK: Worker polls DB every 60s (if Redis pub/sub fails)
```

### Cấu trúc file
```
supabase/migrations/
  0026_service_routing_config.sql       (NEW) - table + 8 features seed + pg_notify trigger

apps/api/services/
  cache.py                              (NEW) - Redis pub/sub wrapper
  routing.py                            (NEW) - get_routing_config(feature) with cache 60s

apps/worker/services/
  config_watcher.py                     (NEW) - subscribe + polling fallback

apps/api/routers/
  admin_routing.py                      (NEW) - 5 endpoints

apps/api/modules/transcript/
  engine.py                             (UPDATE) - use routing.get_routing_config
apps/api/modules/voice/
  routes.py                             (UPDATE) - TTS provider from routing
apps/api/modules/rag/
  embedder.py                           (UPDATE) - embedding provider from routing
apps/worker/tasks/
  script_generate.py                    (UPDATE) - LLM provider from routing
  analysis_task.py                      (UPDATE) - emotion classifier from routing

apps/api/main.py                        (UPDATE) - mount router + register worker boot
apps/web/app/api/admin/routing-config/
  route.ts                              (NEW) - GET list
  [feature]/route.ts                    (NEW) - GET/PATCH
  [feature]/reload/route.ts             (NEW) - POST reload

apps/web/app/(admin)/admin/routing/
  page.tsx                              (NEW) - 8 cards UI

apps/web/app/(admin)/layout.tsx         (UPDATE) - enable Routing
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Worker polling DB mỗi 5s (ĐÃ LOẠI)
- **Lý do loại:** Quá nhiều query. Redis pub/sub là pattern chuẩn cho hot-reload.

### Phương án B — Restart worker mỗi lần admin save (ĐÃ LOẢI)
- **Lý do loại:** Worker restart mất 30s + drop job đang chạy. UX kém.

### Phương án C — In-memory cache không sync giữa nhiều worker (ĐÃ LOẢI)
- **Lý do loại:** Multi-worker setup sẽ có config drift. Redis pub/sub đảm bảo tất cả worker nhận signal cùng lúc.

### Phương án D — Phase 8 refactor consumer Phase 8 (KHÔNG xong) + Phase 9 thêm hot-reload (ĐÃ LOẢI)
- **Lý do loại:** Phase 8 có đủ scope để vừa refactor vừa hot-reload.

### Lý do chọn phương án hiện tại
- **Hot-reload:** Redis pub/sub + Postgres trigger pg_notify (atomic guarantee).
- **Fallback:** Worker poll 60s (không bao giờ stale > 60s).
- **Graceful degradation:** Nếu routing fail → consumer dùng env var cũ (backward compatible).

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Worker refactor gây regression TTS/Transcript | **Cao** | Step 5-9 giữ `if routing config fail → use env var` path. Run existing test suite. |
| 2 | Redis pub/sub channel không deliver (Redis down) | Trung bình | Fallback polling 60s đảm bảo stale ≤ 60s. |
| 3 | Worker reload race condition (2 worker reload cùng lúc) | Thấp | Idempotent — reload chỉ SELECT + cache. |
| 4 | Cost estimate query 7d chậm (> 1s) | Thấp | Cache estimate 5 phút. Index `idx_usage_logs_feature_time`. |
| 5 | Migration trigger pg_notify fail trên môi trường không enable LISTEN | Thấp | Trigger wrap try/catch. Fallback manual reload. |
| 6 | Refactor `transcript/engine.py` mất `tier_used` field (Phase 1 contract) | **Cao** | Giữ nguyên field `tier_used` + `estimated_cost_usd` trong response. |
| 7 | Admin save UI nhầm → worker pick provider sai → job fail | Trung bình | Phase 8 doc warning. Phase 9+ thêm confirm dialog + provider test trước save. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~1200 lines (50 SQL + 250 Python services + 300 Python refactor + 350 TypeScript + 250 markdown) |
| **Timeline** | 15 steps MSEW, ước tính 8-10 giờ Tier 2 thực thi + verify |
| **Files touched** | 11 NEW + 7 UPDATE (1 migration + 3 services + 1 router + 3 proxy + 1 UI + 1 sidebar + 5 consumer + 1 main.py) |

## 6. Phụ thuộc giữa các Step
- Step 1 (migration) → trigger tạo ngay.
- Step 2 (cache) → Step 3 (routing) dùng cache.
- Step 3 (routing) → Step 4 (config_watcher) dùng routing.invalidate_cache().
- Step 5-9 (5 consumer refactor) độc lập nhau → Tier 2 có thể parallel nếu muốn.
- Step 10 (router) → Step 11 (mount + worker boot).
- Step 12 (web proxy) → Step 13 (UI page).
- Step 14 (sidebar) sau Step 13.
- Step 15 (verify hot-reload) cuối cùng.

## 7. Edge cases đặc biệt
- **Worker boot sequence:** Khi celery worker start, KHÔNG tự động load routing config — chỉ subscribe channel. First consumer call sẽ trigger lazy load.
- **Redis channel name:** `routing:config:update` (giữ nguyên convention từ admin_panel_plan.md mục 2.3).
- **Polling fallback:** Worker thread `threading.Thread(daemon=True)` poll DB mỗi 60s, check `updated_at > last_known`.
- **Worker chạy dev (single process):** Vẫn dùng threading.Thread cho watcher.
- **Worker chạy production (multi-process):** Mỗi process có watcher riêng. Redis đảm bảo sync.