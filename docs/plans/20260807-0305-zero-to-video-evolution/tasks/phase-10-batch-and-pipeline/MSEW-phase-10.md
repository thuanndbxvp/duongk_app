# MSEW: Phase 10 — Batch

## Micro-Steps

### Step 1: Migration `0030_batch_production.sql`
Như `phase-10-batch-and-pipeline-mvp.md` mục "Data model".

### Step 2: Pydantic schemas
- `BatchCreate`, `BatchResponse`, `BatchItemResponse`, `CostEstimate`.

### Step 3: cost_estimator
```python
def estimate_batch(plan: BatchPlan) -> CostEstimate:
    # pricing table versioned
    # return total + per-item + blocking_factors
```

### Step 4: provider_health
- Poll 60s; lưu `provider_health_snapshots`.

### Step 5: batch_fanout
```python
async def run(batch_id: UUID):
    for item in batch.items:
        for provider in [item.primary] + fallback_chain:
            if not is_healthy(provider): continue
            if not has_quota(provider, estimate): continue
            try:
                await run_provider(provider, item)
                break
            except TransientError: retry once
            except QuotaError: mark provider exhausted
            except PermanentError: item failed, break
```

### Step 6: API
- `POST /api/batches` (create), `GET /api/batches/{id}`, `POST /api/batches/{id}/approve`, `POST /api/batches/{id}/cancel`, `GET /api/batches/{id}/export.csv`.

### Step 7: UI
- Batch planner: chọn projects → preview cost → approve → theo dõi per-item progress.

### Step 8: Tests
```powershell
pytest tests/worker/test_batch_fanout.py -v --cov=apps.worker.services.batch_fanout --cov=apps.worker.services.cost_estimator
```
- Cost estimator idempotent.
- Fallback chain đúng thứ tự.
- Partial success: 1 item fail → các item khác vẫn success.
- Max 3 retries/item.