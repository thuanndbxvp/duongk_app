# Phase 1 — Acceptance Criteria

> **Audience**: Tier 2 (implementer) + Tier 1 (reviewer)
> **Format**: Checklist có thể tick `x` khi verify

---

## A. Drift fixes

### A.1 — `POST /api/insights/{id}/approve` → `/api/insights/{id}/decision`

- [ ] FE call đổi thành `POST /api/insights/{id}/decision` với body `{decision: "approved"}`
- [ ] Test: gọi từ `/assistants/[id]/insights` page → insight status = approved
- [ ] Tương tự cho `decision: "rejected"`
- [ ] Browser DevTools Network: response 200 OK

### A.2 — `POST /api/batches/{id}/cancel` → verify path

- [ ] Đọc `apps/api/routers/batch.py` để confirm route hiện tại
- [ ] Nếu có `POST /api/batches/{id}/cancel` → FE OK, không fix
- [ ] Nếu không có → đổi FE call thành `POST /api/jobs/{id}/cancel` (single job cancel)
- [ ] Test: cancel batch → batch status = cancelled

### A.3 — `POST /api/admin/mfa/enroll` → `/api/admin/mfa`

- [ ] FE call đổi thành `POST /api/admin/mfa` (đã là POST no path)
- [ ] Test: enroll MFA → returns QR + backup codes
- [ ] Verify endpoint `POST /api/admin/mfa` có trong OpenAPI

### A.4 — Verification matrix cho 9 cases còn lại

| Drift | Decision | Document |
|---|---|---|
| `GET /api/jobs?assistant_id=...` | Add `GET /api/jobs?assistant_id=` to backend (Tier 1 escalate) | Appendix A |
| `POST /api/insights/{id}/to-project` | Verify path exists in modules | Appendix A |
| `GET /api/assistants/{id}/insights` | Verify path exists | Appendix A |
| `POST /api/assistants/{id}/ingest` | Verify path exists | Appendix A |
| `POST /api/assets/upload-init` | Add backend route (Tier 1 escalate) | Appendix A |
| `POST /api/assets/upload-complete` | Add backend route (Tier 1 escalate) | Appendix A |
| `GET /api/projects/{id}/timeline` | Verify exists in voice router | Appendix A |
| `GET /api/projects/{id}/exports` | Verify exists | Appendix A |
| `GET /api/projects/{id}/lab/*` | Verify exists | Appendix A |

## B. Cancel Render Job UI

### B.1 — Component

- [ ] File `apps/web/components/cancel-render-button.tsx` exists
- [ ] Component exported với Props: `{projectId, jobId, status}`
- [ ] Returns null nếu status không phải 'running'/'pending'
- [ ] Click button → mở ConfirmDialog
- [ ] Confirm → call `POST /api/jobs/{jobId}/cancel`
- [ ] Loading state spinner + button disabled
- [ ] Error handling: alert hoặc toast notification

### B.2 — Integration

- [ ] Wire vào `<VideoPreview>` component
- [ ] Hiển thị button khi `currentJob.status ∈ {running, pending}`
- [ ] Sau cancel: status đổi sang 'cancelled' trong <5s
- [ ] Video preview area: thông báo "Render bị hủy", xóa download link

### B.3 — Test

- [ ] Unit test: `<CancelRenderButton>` reacts đúng với status prop
- [ ] Integration test: mock cancel job → verify poll mechanism
- [ ] E2E test (optional): tạo project → start render → cancel giữa chừng → verify status

## C. Dead services cleanup

### C.1 — Decision matrix

| Service | Decision | Reason |
|---|---|---|
| `backup.py` | KEEP | Will be used in P6 admin |
| `usage_tracker.py` | KEEP | Decorator chờ apply |
| `config_watcher.py` | WIRE | Used in P1 (step D) |
| `media_pipeline.py` | KEEP | FFmpeg helpers centralization |
| `youtube.py` | REMOVE | Dead code, no consumers |
| `comments_provider.py` | KEEP | Used by `ingest_comments.py` task |

### C.2 — Remove `youtube.py`

- [ ] `grep -r "from apps.api.services.youtube" apps/ tests/` → 0 results
- [ ] `git rm apps/api/services/youtube.py`
- [ ] Update imports in any tests that referenced it
- [ ] Test all pass

### C.3 — Document KEEP services

- [ ] Add docstring header mỗi file: purpose + when used + who maintains
- [ ] Mark TODO: nếu schedule integrate trong phase nào

## D. config_watcher wire

### D.1 — Wire trong Celery worker

- [ ] Signal `worker_ready` registered in `celery_app.py`
- [ ] On worker boot: `start_watcher()` called
- [ ] Log: `[config_watcher] Started on worker boot` (or similar)
- [ ] Graceful failure: nếu Redis down → log warning, continue

### D.2 — Test

- [ ] Unit test: simulate cell boot → verify watcher started
- [ ] Integration test: change routing config in DB → verify cache invalidated <5s
- [ ] Verify TTL fallback (60s polling) works when Redis pub/sub down

## E. Final verification

- [ ] `pytest tests/` → ≥80% pass
- [ ] `bash scripts/run_e2e_local.sh` → exit 0
- [ ] LoC: ~150 added, ~100 removed (net positive cleanup)
- [ ] No new dependencies added
- [ ] Tier 1 sign-off

---

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ |
| Reviewer | _Tier 1_ | ____ | ☐ |
