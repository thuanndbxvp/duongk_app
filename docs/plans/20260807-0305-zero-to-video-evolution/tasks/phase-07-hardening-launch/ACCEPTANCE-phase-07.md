# ACCEPTANCE: Phase 07 — Hardening

## 1. Functional
- [ ] Mọi worker có structured log event.
- [ ] Prometheus metrics expose đúng các chỉ số ở PLAN.
- [ ] Rate limit + CORS hoạt động đúng.
- [ ] Audit log ghi đầy đủ.
- [ ] Billing hold/commit/refund idempotent.
- [ ] Dead-letter queue có retry policy đúng.
- [ ] E2E test full pipeline pass.
- [ ] Load smoke pass.

## 2. Non-functional
- [ ] Không có P0 issue mới.
- [ ] Cost estimate sai số < 20%.
- [ ] RLS test xanh 100%.

## 3. Coverage
- ≥80% cho module mới.

## 4. Done
- All pass + AUDIT-REPORT nộp + release-gates doc đầy đủ.