# SKILL-ROUTING: Phase 10 — Batch

## Per-step

| Step | Task | Primary | Reference | Fallback |
|---|---|---|---|---|
| 1 | Migration `batch_runs`, `batch_items`, `provider_health_snapshots`, `batch_cost_estimates` | `databases` | `backend-development` | `debugging` |
| 2 | Pydantic schemas batch | `backend-development` | `databases` | `debugging` |
| 3 | `cost_estimator.py` với provider pricing table version | `backend-development` | `planning` | `debugging` |
| 4 | `provider_health.py` poll 60s | `backend-development` | `planning` | `debugging` |
| 5 | `batch_fanout.py` với concurrency + fallback decision | `backend-development` | `planning` | `debugging` |
| 6 | API batch endpoints | `backend-development` | `databases` | `debugging` |
| 7 | UI batch planner | `frontend-development` | `ui-styling` | `aesthetic` |
| 8 | Tests cost estimator idempotent + fallback + partial success | `testing-protocol` | `debugging-protocol` | `debugging` |