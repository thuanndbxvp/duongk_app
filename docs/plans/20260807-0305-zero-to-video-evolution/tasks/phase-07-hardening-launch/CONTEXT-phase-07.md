# CONTEXT: Phase 07 — Hardening, Observability, Billing, Launch

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Codebase
- Toàn bộ Phase 01–06 đã merged.
- `jobs`, `credit_transactions`, `services/audit_log.py` có sẵn.

## 3. Files
### Modify
- Mọi worker tasks (thêm structured logging).
- Mọi routers (rate-limit, CORS, audit hook).

### Create
- `apps/worker/services/observability.py`
- `apps/worker/services/billing.py` (refactor từ `credit_transactions`)
- `apps/api/middleware/rate_limit.py`
- `apps/api/middleware/cors_allowlist.py`
- `tests/e2e/test_pipeline_e2e.py`
- `tests/load/test_render_queue.py`

## 4. Dependencies
- prometheus_client, opentelemetry, sentry-sdk (optional).

## 5. Ràng buộc
- Release gates bắt buộc trước production.
- E2E test cover full pipeline blank project → export.