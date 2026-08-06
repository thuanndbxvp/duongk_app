# MSEW: Phase 07 — Hardening

## Micro-Steps

### Step 1: Structured logging
- Mọi worker emit JSON event: `project_stage_started/completed/failed`, `provider_call_started/completed/failed`, `asset_materialized`, `tts_duration_measured`, `render_progress`, `render_cancelled`, `export_verified`.

### Step 2: Prometheus metrics
- `stage_latency_seconds` histogram (label: stage).
- `provider_success_total` counter.
- `cost_per_video_cents` histogram.
- `tts_queue_wait_seconds`.
- `render_failure_total`, `render_cancelled_total`.
- `asset_orphan_count` gauge.

### Step 3: Rate limit + CORS
- `slowapi` cho FastAPI: 60 req/min/user cho write endpoints, 600 req/min/user cho read.
- CORS allowlist domains qua env.

### Step 4: Audit log + content policy
- Mọi AI generation → content policy check trước.
- Audit log: ai, lúc nào, action, asset_id.

### Step 5: Billing
- `hold_credits(user_id, estimated_cents)` trước job.
- `commit_credits(user_id, actual_cents)` khi success.
- `refund_credits(user_id, held_cents - actual_cents)` khi fail.
- Không charge khi provider fail trước khi tạo output.

### Step 6: Dead-letter + retry
- Phân loại: transient (retry), permanent (dead-letter), quota (retry sau N phút).
- Max 3 retry, backoff exponential.

### Step 7: E2E test
- `tests/e2e/test_pipeline_e2e.py`: blank project → approve → voice → asset → render → export → verify MP4.

### Step 8: Load smoke
- 20 render jobs đồng thời; verify queue không quá tải.

### Step 9: Release gates + rollback
- Document: `docs/operations/release-gates.md` và `docs/operations/rollback-procedure.md`.

```powershell
pytest tests/e2e/ tests/load/ -v
```