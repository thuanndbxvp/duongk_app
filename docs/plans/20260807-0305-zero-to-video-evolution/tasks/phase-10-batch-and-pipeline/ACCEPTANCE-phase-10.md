# ACCEPTANCE: Phase 10 — Batch

## 1. Functional
- [ ] User thấy tổng chi phí ước tính trước khi Run.
- [ ] Provider chính hết quota → fallback.
- [ ] 1 item fail → các item khác OK (continue_on_error).
- [ ] Cancel batch dừng item chưa start.
- [ ] Cost actual không vượt estimate quá 20%.
- [ ] CSV export success/failed items.

## 2. Non-functional
- [ ] Per-project concurrency ≤ 2.
- [ ] Global render max 4.
- [ ] Max 50 items/batch.
- [ ] Max 3 retries/item.

## 3. Coverage
- ≥80% cho module mới.

## 4. Done
- All pass + AUDIT-REPORT.