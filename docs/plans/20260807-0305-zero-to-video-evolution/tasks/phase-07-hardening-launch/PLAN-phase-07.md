# PLAN: Phase 07 — Hardening & Launch

## 1. Mục tiêu
- **Mô tả:** Zero-to-Video từ beta → production-ready: idempotency, retry policy, observability, billing rõ ràng, security cứng, E2E test.
- **Giá trị:** Có thể launch tự tin; SLA đo được; rollback an toàn.

## 2. Trọng tâm
- **Idempotency** khắp nơi (create project, provider call, upload, TTS, render).
- **Outbox** hoặc retry-safe stage events.
- **Reconcile** job DB ↔ Celery result.
- **Cleanup** temp files + orphaned R2 objects.
- **Resume** từ stage cuối completed.
- **Per-stage timeout.**

## 3. Release gates
- Không còn P0 security/reliability issue.
- Draft render pass fixture suite.
- Cancel test chứng minh FFmpeg dừng.
- Output package verify được.
- Cost estimate sai số < 20%.
- RLS test không rò project/asset.
- Có rollback migration + cleanup procedure.

## 4. Rủi ro
| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Migration phá data | Cao | Backward-compatible nullable FK; rollback script test trên staging. |
| Outbox missed event | Trung bình | Idempotency + reconcile job hàng giờ. |
| Orphan R2 objects | Trung bình | Cron cleanup soft-deleted > 30 ngày. |

## 5. Nỗ lực
- ~900 LOC + 1 tuần test/verify.