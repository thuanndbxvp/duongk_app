# Phase 07 — Hardening, observability, billing và launch

## Mục tiêu

Đưa Zero-to-Video từ feature beta thành pipeline có thể vận hành ổn định.

## Reliability

- Idempotency key cho create project, provider call, upload materialize, TTS và render.
- Outbox hoặc retry-safe stage events.
- Reconcile job DB với Celery result.
- Dead-letter/retry policy theo lỗi transient/permanent.
- Cleanup temp files và orphaned R2 objects.
- Resume từ stage cuối completed.
- Per-stage timeout.

## Security

- RLS cho projects/scenes/assets/timelines/exports.
- Presigned R2 URLs ngắn hạn.
- Validate file type bằng magic bytes.
- Giới hạn upload size/duration.
- Không log secrets, prompt có PII hoặc signed URLs.
- CORS allowlist, webhook signature verification.
- Provider keys chỉ ở server/Vault.
- Audit log cho cost, asset processing, export và delete.
- Content policy trước AI generation và cleanup.

## Observability

Structured events:

- `project_stage_started/completed/failed`.
- `provider_call_started/completed/failed`.
- `asset_materialized`.
- `tts_duration_measured`.
- `render_progress`.
- `render_cancelled`.
- `export_verified`.

Metrics:

- Stage latency p50/p95.
- Provider success/fallback rate.
- Cost per completed video.
- TTS queue wait.
- Render failure/cancel rate.
- Asset orphan count.
- Time from topic to draft.

## Billing

Tái sử dụng credit hold/partial commit/release của appDK.

Mỗi job phải khai báo:

- Estimated credits.
- Actual provider cost.
- Held credits.
- Committed credits.
- Refunded credits.

Không charge user khi provider fail trước khi tạo output.

## Test strategy

- Unit: schema, timeline compiler, duration recalculation, provider adapters, scoring.
- Integration: RLS, R2 signed URLs, Celery job state, credit RPC.
- Media integration: render 3 fixture scenes, verify ffprobe.
- Failure tests: timeout, cancel, provider 429, corrupt upload, missing asset, partial batch.
- E2E: blank project → export package.
- Load smoke: nhiều TTS/render jobs trên queue limits.

## Release gates

- Không còn P0 security/reliability issue.
- Draft render thành công trên fixture suite.
- Cancel test chứng minh FFmpeg process dừng.
- Output package verify được.
- Cost estimate sai số trong ngưỡng đã quyết định.
- RLS test không rò project/asset của user khác.
- Có rollback migration và cleanup procedure.
