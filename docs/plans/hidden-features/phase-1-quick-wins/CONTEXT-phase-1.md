# Phase 1 — Context & Background

## 1. Why this phase exists

Tier 1 audit ngày 2026-08-07 phát hiện "hidden features" — backend code hoàn chỉnh nhưng frontend không có UI access. Phase 1 là **foundation** — phải fix drift và cleanup dead code trước khi build features mới (drift có thể gây 404 không mong muốn; dead code tăng maintenance cost).

## 2. Background: Drift là gì?

Trong quá trình iterate (Phase 1-12), backend team refactor rename endpoints nhiều lần. Frontend cache references cũ. Khi user click button trong UI:
- Backend không có route → 404 Not Found
- Hoặc route có nhưng response shape khác → bug logic

Tier 1 liệt kê 12 cases; 3 là critical (block user flow), 9 là cosmetic (chưa ai click).

### Critical drift (3 cases, fix trong P1)

1. **Insights approve**: FE gọi `/approve` (T02 init), backend đổi tên `/decision` (T02 final). Block: user không approve được insights.
2. **Batch cancel**: FE gọi `/api/batches/{id}/cancel` (Phase 3 spec), backend mount riêng job-level cancel. Block: user không cancel được batch.
3. **MFA enroll**: FE gọi `/api/admin/mfa/enroll` (Phase 9 spec), backend mount `/api/admin/mfa` (POST no path). Block: admin không enroll MFA được.

### Cosmetic drift (9 cases, document trong Appendix A)

E.g. `POST /api/assets/upload-init` — backend chưa có route, nhưng feature Asset Drawer hiện vẫn work bằng direct upload to storage_key. Tier 1 escalate lên backend team; trong P1 chỉ document.

## 3. Background: Cancel Render Job

Trong production, user cần cancel render mid-flight (e.g., nhận ra sai script, muốn đổi voice). Backend đã implement từ Phase 4 (`POST /api/jobs/{job_id}/cancel` trong `routers/render.py:76`). Nhưng frontend `<VideoPreview>` chỉ show status, không có button.

**Critical vì**: render job chạy 5-30 phút. Không có cancel = waste credits + GPU time.

## 4. Background: Dead services

Tier 1 grep `from apps.X.services.Y import` cho thấy 6 files không ai import ngoài tests:

| Service | Created in | Use case | Decision |
|---|---|---|---|
| `apps/api/services/backup.py` | Phase 9 plan | Admin backup config JSON | KEEP (P6) |
| `apps/api/services/usage_tracker.py` | Phase 7 plan | Decorator `@track_usage` | KEEP (deferred) |
| `apps/worker/services/config_watcher.py` | Phase 8 plan | Worker subscribe Redis pub/sub | WIRE (P1) |
| `apps/worker/services/media_pipeline.py` | Phase 2 | FFmpeg helpers | KEEP (shared) |
| `apps/api/services/youtube.py` | Phase 1 init | Old transcript helper | REMOVE |
| `apps/worker/services/comments_provider.py` | Phase 6 | Comments fetching | KEEP (used by task) |

Mục tiêu P1: **commit decision matrix** cho 6 files, wire `config_watcher`, remove `youtube.py`.

## 5. Background: config_watcher.py

`apps/worker/services/config_watcher.py` là worker-side cache invalidation cho admin routing config. Khi admin thay đổi routing config qua UI:
1. Backend update DB → publish Redis message `routing:config:update`
2. Worker subscriber nhận → invalidate in-memory cache
3. Lần call tiếp theo của worker sẽ re-fetch từ DB

Code full, nhưng `start_watcher()` chưa được gọi → worker không subscribe → cache stale.

**Fix**: Register trong `celery_app.py` `worker_ready` signal → auto-start watcher.

## 6. What is NOT in this phase

- Voice profiles UI (P3)
- Style Bible UI (P4)
- Asset Library (P5)
- Channel Collector (P5)
- Admin backup/traffic pages (P6)
- Database column migrations (P6)

Tier 2 chỉ focus vào 4 tasks trên. Đừng over-engineer.

## 7. References

- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.2 (drift), §5.1 (dead services), §7.1 (bugs)
- `apps/api/routers/render.py` (cancel render route)
- `apps/worker/services/config_watcher.py` (watcher logic)
- `apps/worker/celery_app.py` (worker signals reference)
