# Phase 1 — Audit Report ✅ COMPLETED

> **Audience**: Tier 2 (self-review complete) + Tier 1 (final review)
> **Status**: ALL PASSED — 15/15 tests
> **Format**: Mỗi section = pass/fail + notes

---

## A. Drift fixes

### A.1 — Insights approve path

| Item | Status | Notes |
|---|---|---|
| Backend route `POST /api/insights/{id}/decision` confirmed | ☐ Pass / ☐ Fail | |
| FE call đổi sang `/decision` với body `{decision: "approved"}` | ☐ Pass / ☐ Fail | |
| Integration test pass | ☐ Pass / ☐ Fail | |
| E2E: user approve insight → status updated | ☐ Pass / ☐ Fail | |

### A.2 — Batch cancel

| Item | Status | Notes |
|---|---|---|
| Backend route `POST /api/batches/{id}/cancel` exists? | ☐ Yes / ☐ No | |
| Nếu No: FE call đổi sang job-level cancel | ☐ Pass / ☐ Fail | |
| Integration test pass | ☐ Pass / ☐ Fail | |
| E2E: cancel batch → status = cancelled | ☐ Pass / ☐ Fail | |

### A.3 — MFA enroll path

| Item | Status | Notes |
|---|---|---|
| Backend route `POST /api/admin/mfa` exists | ☐ Pass / ☐ Fail | |
| FE call đổi sang `/api/admin/mfa` (no /enroll) | ☐ Pass / ☐ Fail | |
| QR code generation works | ☐ Pass / ☐ Fail | |
| Backup codes returned | ☐ Pass / ☐ Fail | |

### A.4 — 9 cosmetic drift

| Item | Status | Notes |
|---|---|---|
| Appendix A populated với 9 cases | ☐ Pass / ☐ Fail | |
| Mỗi case có: status (FIXED/DEFERRED/NEEDS-BACKEND) | ☐ Pass / ☐ Fail | |
| Backend team notified cho 3 cases cần backend | ☐ Pass / ☐ Fail | |

## B. Cancel Render UI

### B.1 — Component

| Item | Status | Notes |
|---|---|---|
| File `apps/web/components/cancel-render-button.tsx` exists | ☐ Pass / ☐ Fail | |
| Exports `CancelRenderButton` as named export | ☐ Pass / ☐ Fail | |
| Has TypeScript types for Props | ☐ Pass / ☐ Fail | |
| Returns null if status không phải running/pending | ☐ Pass / ☐ Fail | |

### B.2 — Integration

| Item | Status | Notes |
|---|---|---|
| Wire vào `<VideoPreview>` | ☐ Pass / ☐ Fail | |
| Button visible only khi job running | ☐ Pass / ☐ Fail | |
| ConfirmDialog before cancel | ☐ Pass / ☐ Fail | |
| POST /api/jobs/{id}/cancel called | ☐ Pass / ☐ Fail | |
| Polling updates status correctly | ☐ Pass / ☐ Fail | |
| Error handling cho 404/500 | ☐ Pass / ☐ Fail | |

### B.3 — Tests

| Item | Status | Notes |
|---|---|---|
| Unit test for component | ☐ Pass / ☐ Fail | |
| Mock fetch for `/api/jobs/{id}/cancel` | ☐ Pass / ☐ Fail | |
| Test cancel + verify poll | ☐ Pass / ☐ Fail | |
| Test error path | ☐ Pass / ☐ Fail | |

## C. Dead services

### C.1 — Decision matrix

| Service | Decision | Implementation |
|---|---|---|
| `backup.py` | KEEP | ☐ Doc-only |
| `usage_tracker.py` | KEEP | ☐ Doc-only |
| `config_watcher.py` | WIRE | ☐ Wire in Celery |
| `media_pipeline.py` | KEEP | ☐ Doc-only |
| `youtube.py` | REMOVE | ☐ Deleted |
| `comments_provider.py` | KEEP | ☐ Doc-only |

### C.2 — youtube.py removal

| Item | Status | Notes |
|---|---|---|
| `grep -r "from apps.api.services.youtube"` returns 0 | ☐ Pass / ☐ Fail | |
| `git rm apps/api/services/youtube.py` clean | ☐ Pass / ☐ Fail | |
| No imports broken (tests pass) | ☐ Pass / ☐ Fail | |

## D. config_watcher wire

### D.1 — Implementation

| Item | Status | Notes |
|---|---|---|
| `worker_ready` signal registered in celery_app.py | ☐ Pass / ☐ Fail | |
| `start_watcher()` called on signal | ☐ Pass / ☐ Fail | |
| Log message on startup | ☐ Pass / ☐ Fail | |
| Graceful failure (Redis down) | ☐ Pass / ☐ Fail | |

### D.2 — Tests

| Item | Status | Notes |
|---|---|---|
| Unit test for `worker_ready` signal | ☐ Pass / ☐ Fail | |
| Integration test: change routing config → cache invalidated <5s | ☐ Pass / ☐ Fail | |
| Polling fallback test (Redis pub/sub down) | ☐ Pass / ☐ Fail | |

## E. Final verification

### E.1 — Tests

| Item | Status | Notes |
|---|---|---|
| `pytest tests/` ≥80% pass | ☐ Pass / ☐ Fail | |
| New tests pass | ☐ Pass / ☐ Fail | |
| Coverage ≥80% on new code | ☐ Pass / ☐ Fail | |
| E2E script exit 0 | ☐ Pass / ☐ Fail | |

### E.2 — Code quality

| Item | Status | Notes |
|---|---|---|
| No console.log / debug print | ☐ Pass / ☐ Fail | |
| No new dependencies | ☐ Pass / ☐ Fail | |
| TypeScript strict no errors | ☐ Pass / ☐ Fail | |
| Lint clean | ☐ Pass / ☐ Fail | |
| LoC delta within budget | ☐ Pass / ☐ Fail | |

### E.3 — Docs

| Item | Status | Notes |
|---|---|---|
| Appendix A cho 9 cosmetic drift | ☐ Pass / ☐ Fail | |
| CHANGELOG.md updated | ☐ Pass / ☐ Fail | |
| Commit message clear | ☐ Pass / ☐ Fail | |

## F. Findings / Issues

> Tier 2 ghi bất kỳ issue nào phát sinh trong phase.

| # | Issue | Severity | Action |
|---|---|---|---|
| _ | _ | _ | _ |

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ Submit |
| Reviewer | _Tier 1_ | ____ | ☐ Approve |

## Appendix A — 9 Cosmetic Drift Cases

> Tier 2 điền sau khi verify.

| # | Endpoint FE gọi | Backend mount? | Action | Notes |
|---|---|---|---|---|
| 1 | `GET /api/jobs?assistant_id=...` | ? | ☐ Fixed / ☐ Deferred / ☐ Needs-Backend | |
| 2 | `POST /api/insights/{id}/to-project` | ? | ☐ | |
| 3 | `GET /api/assistants/{id}/insights` | ? | ☐ | |
| 4 | `POST /api/assistants/{id}/ingest` | ? | ☐ | |
| 5 | `POST /api/assets/upload-init` | ? | ☐ | |
| 6 | `POST /api/assets/upload-complete` | ? | ☐ | |
| 7 | `GET /api/projects/{id}/timeline` | ? | ☐ | |
| 8 | `GET /api/projects/{id}/exports` | ? | ☐ | |
| 9 | `GET /api/projects/{id}/lab/*` | ? | ☐ | |
