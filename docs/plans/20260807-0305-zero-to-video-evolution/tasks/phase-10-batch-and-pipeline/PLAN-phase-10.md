# PLAN: Phase 10 — Batch

## 1. Mục tiêu
- Cost estimate trước khi chạy batch.
- Provider fallback khi primary fail/hết quota.
- Per-project + global concurrency limit.
- Partial success: 1 item fail không hỏng batch.

## 2. Kiến trúc
```text
Batch plan → cost estimate → dry-run → user approve
  → fan-out per item (queue batch.<kind>)
  → per-item retry / fallback
  → partial summary
```

## 3. Rủi ro
| Rủi ro | Giảm thiểu |
|---|---|
| Provider trả giá động | cap = max(estimate, last_actual * 1.2). |
| Fan-out quá nhiều | max 50 items/batch. |
| Fallback loop vô hạn | max 3 lần/item. |
| Cancel nhưng item đang chạy vẫn tính credit | Hiển thị rõ UI. |