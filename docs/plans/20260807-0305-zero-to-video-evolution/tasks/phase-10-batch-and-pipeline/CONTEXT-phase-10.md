# CONTEXT: Phase 10 — Batch Production, Cost Estimation & Provider Fallback

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Files
### Modify
- `apps/worker/celery_app.py` — thêm queue `batch.<kind>`.
- `apps/api/routers/projects.py` — endpoint batch.

### Create
- `supabase/migrations/0030_batch_production.sql`
- `apps/worker/services/cost_estimator.py`
- `apps/worker/services/provider_health.py`
- `apps/worker/services/batch_fanout.py`
- `apps/worker/tasks/batch_run.py`
- `apps/api/routers/batch.py`
- `apps/api/schemas/batch.py`
- `apps/web/components/batch-planner.tsx`
- `apps/web/app/(dashboard)/batches/page.tsx`
- `tests/worker/test_batch_fanout.py`

## 3. Dependencies
- redis (queue).
- csv export.

## 4. Ràng buộc
- Per-project concurrency max 2; global render max 4.
- Max 50 items/batch.
- Max 3 retries/item.
- Credit hold toàn batch trước khi start.
- Cost estimate hiển thị `model_version` + `captured_at`.