# Phase 10 — Batch production, cost estimation và provider fallback

## Context

- §10 P2 trong `Main-idea.md` đề xuất batch video generation + cost estimation + provider fallback.
- `plan.md` đã có ưu tiên Batch production nhưng đặt ở phase sau.
- Hiện appDK có `credit_transactions` và provider routing sẵn (`api_provider_keys`); chưa có cơ chế cost estimate và fallback matrix.

## Mục tiêu

Cho phép người dùng chạy nhiều dự án / nhiều video cùng lúc với:

1. Ước lượng chi phí trước khi chạy.
2. Provider fallback khi provider chính lỗi / hết quota.
3. Concurrency limit per-project và global.
4. Partial success: lỗi một item không làm hỏng batch.

```text
Batch plan
  → cost estimate
  → dry-run validation
  → user approve
  → fan-out per item (queue riêng)
  → per-item retry / fallback
  → partial summary
```

## Data model

Tạo migration `0030_batch_production.sql` với:

- `batch_runs`:
  - `id`, `owner_id`, `kind` (`ideas` | `scripts` | `scenes` | `assets` | `tts` | `render`).
  - `status` (`draft` | `estimated` | `approved` | `running` | `partial_success` | `success` | `failed` | `cancelled`).
  - `cost_estimate_cents`, `cost_actual_cents`.
  - `concurrency_limit`, `global_rate_limit`.
  - `approved_at`, `started_at`, `finished_at`.
  - `failure_policy` (`abort_on_first` | `continue_on_error`).
- `batch_items`:
  - `id`, `batch_id`, `project_id`, `target_id`, `target_kind`, `position`.
  - `status` (`pending` | `running` | `success` | `failed` | `skipped` | `cancelled`).
  - `primary_provider`, `fallback_provider`, `attempt_count`.
  - `error_code`, `error_message`.
  - `cost_actual_cents`.
  - `started_at`, `finished_at`.
- `provider_health_snapshots`:
  - `provider`, `captured_at`, `p50_ms`, `p95_ms`, `error_rate`, `quota_left`.
  - Dùng cho cost estimate và decision fallback.
- `batch_cost_estimates`:
  - `batch_id`, `item_id`, `provider`, `estimated_cents`, `model_version`, `captured_at`.

## Cost estimator contract

```text
estimate_batch(batch_plan) -> {
  total_cents,
  per_item: [{target_id, provider, estimated_cents, risk_level}],
  blocking_factors: ["provider_x quota low", "user_credits low"]
}
```

## Fallback decision

```text
try(item):
  primary_provider = item.primary_provider
  for provider in [primary, *fallback_chain]:
    if not is_healthy(provider): continue
    if not has_quota(provider, cost_estimate): continue
    try: run(provider)
    except TransientError: retry once
    except QuotaError: mark provider exhausted, try next
    except PermanentError: mark item failed, break
```

## Implementation steps

1. Migration cho 4 bảng trên.
2. `cost_estimator.py` với provider pricing table có version.
3. `provider_health.py` poll mỗi 60s; lưu `provider_health_snapshots`.
4. Batch fan-out worker với queue `batch.<kind>` (tách khỏi queue render chính).
5. Concurrency guard theo `batch_runs.concurrency_limit` và global rate limit.
6. UI: chọn nhiều project → preview cost → approve → theo dõi per-item progress.
7. CSV / JSON export danh sách item success/failed.
8. Tests: cost estimator idempotent, fallback đúng thứ tự, partial success.

## Acceptance criteria

- User nhìn thấy tổng chi phí ước tính trước khi bấm Run.
- Khi provider chính hết quota, batch tự động chuyển sang fallback.
- Lỗi 1 item không huỷ các item khác (nếu `continue_on_error`).
- Cancel batch dừng các item chưa start; item đang chạy chờ ack hiện tại xong.
- Cost actual không vượt cost estimate quá 20% (cảnh báo nếu vượt).
- Batch summary có thể tải CSV cho kế toán.

## Guardrails

- Credit hold toàn batch trước khi start; commit từng item khi success; refund khi fail.
- Per-project concurrency max 2; global render max 4; user có thể giảm.
- Provider call phải qua adapter chính thức, không có private endpoint.
- Cost estimate hiển thị rõ `model_version` và `captured_at`; cảnh báo nếu > 24h.

## Risks

- Provider trả giá động → estimate lệch: cap theo max(estimate, last_actual * 1.2).
- Fan-out quá nhiều làm nghẽn Redis: giới hạn max items/batch = 50.
- Fallback loop vô hạn nếu tất cả provider fail: max 3 lần thử / item.
- Batch cancelled nhưng item đang chạy vẫn tính credit: hiển thị rõ trong UI.

## Phụ thuộc

- Phase 04: render registry có cancel thật (đã có trong plan).
- Phase 05: provider routing đầy đủ.
- Phase 06: batch production scope.
- Phase 08: insight → idea → project seed từ insight.