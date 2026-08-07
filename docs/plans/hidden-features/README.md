# Hidden Features Implementation Roadmap — Tier 2 Handoff

> **Audience**: Tier 2 (engineer sẽ execute implementation)
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` (Tier 1 audit ngày 2026-08-07)
> **Status**: Ready for execution
> **Total effort**: ~21 ngày (6 phases)

---

## 🎯 Vấn đề

Audit 2026-08-07 phát hiện **~45 backend endpoints** đã code nhưng **không có UI**. Đây là "hidden features" — user không thể access vì không có button/form. Nguyên nhân: backend team deliver xong các phase nhưng frontend wire-up chưa kịp.

## 🗺️ Phase breakdown

| Phase | Tên | Effort | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| **P1** | Foundation + Quick Wins | 2 ngày | — | 🟢 Ready |
| **P2** | Wire Existing Components | 3 ngày | P1 | 🟢 Ready |
| **P3** | Voice Profiles Page | 4 ngày | P1 | 🟢 Ready |
| **P4** | Style Bible UI | 5 ngày | P2 | 🟢 Ready |
| **P5** | Asset Library + Channel Collector | 4 ngày | P1 | 🟢 Ready |
| **P6** | Admin Tools + Cleanup | 3 ngày | P1 | 🟢 Ready |

Total: **21 ngày** (3 tuần part-time hoặc 1 sprint full-time).

## 📂 Cấu trúc tài liệu

Mỗi phase có 1 file PLAN + 1 file ACCEPTANCE + 1 file CONTEXT + 1 file MSEW + 1 file AUDIT-REPORT:

```
docs/plans/hidden-features/
├── README.md                                  ← (file này)
├── 00-roadmap.md                              ← Tổng quan + decision log
├── phase-1-quick-wins/
│   ├── PLAN-phase-1.md
│   ├── ACCEPTANCE-phase-1.md
│   ├── CONTEXT-phase-1.md
│   ├── MSEW-phase-1.md
│   └── AUDIT-REPORT-phase-1.md
├── phase-2-wire-existing/
│   ├── PLAN-phase-2.md
│   ├── ACCEPTANCE-phase-2.md
│   ├── CONTEXT-phase-2.md
│   ├── MSEW-phase-2.md
│   └── AUDIT-REPORT-phase-2.md
├── phase-3-voice-profiles/
│   ├── PLAN-phase-3.md
│   ├── ACCEPTANCE-phase-3.md
│   ├── CONTEXT-phase-3.md
│   ├── MSEW-phase-3.md
│   └── AUDIT-REPORT-phase-3.md
├── phase-4-style-bible/
│   ├── PLAN-phase-4.md
│   ├── ACCEPTANCE-phase-4.md
│   ├── CONTEXT-phase-4.md
│   ├── MSEW-phase-4.md
│   └── AUDIT-REPORT-phase-4.md
├── phase-5-asset-channel/
│   ├── PLAN-phase-5.md
│   ├── ACCEPTANCE-phase-5.md
│   ├── CONTEXT-phase-5.md
│   ├── MSEW-phase-5.md
│   └── AUDIT-REPORT-phase-5.md
└── phase-6-admin-cleanup/
    ├── PLAN-phase-6.md
    ├── ACCEPTANCE-phase-6.md
    ├── CONTEXT-phase-6.md
    ├── MSEW-phase-6.md
    └── AUDIT-REPORT-phase-6.md
```

## 📋 Kế hoạch tier-2 execute

Tier 2 chọn 1 phase, đọc `PLAN-phase-N.md` → `ACCEPTANCE-phase-N.md` → implement theo `MSEW-phase-N.md` → verify qua `AUDIT-REPORT-phase-N.md`.

Sequence đề xuất:
1. **P1 trước** (foundation, tạo sao cho codebase clean)
2. **P2 + P3 song song** (nếu có 2 devs)
3. **P4** sau P2 (analysis tabs wire xong thì style bible mới có nghĩa)
4. **P5 + P6** cuối (cosmetic + ops)

## 🔑 Nguyên tắc cho Tier 2

1. **KHÔNG sửa backend API contract** — chỉ wrap existing endpoints. Nếu cần đổi, escalate.
2. **Match existing UI patterns** — dùng `lib/api-client.ts` cho server, `fetch('/api/...')` cho client, `useArrayFetch` cho admin.
3. **Backward compat** — không break existing FE flows.
4. **Test ngay khi build** — không để cuối phase mới test.
5. **Self-review theo AUDIT-REPORT** trước khi xong phase.

## 🎬 Quy trình làm việc

```
Tier 2 đọc PLAN → implement theo MSEW → viết tests
    ↓
Self-review bằng ACCEPTANCE checklist
    ↓
Ghi findings vào AUDIT-REPORT
    ↓
Commit + push branch
    ↓
Báo Tier 1 review → merge
```

## 📊 Success metrics

| Metric | Target |
|---|---|
| Orphan endpoints giảm | Từ 45 → 0 (P1-P3) → còn 0 (P4-P6) |
| Frontend-feasible coverage | 100% routes có ít nhất 1 FE call |
| Drift bugs | 0 (fix tất cả trong P1) |
| Test pass | ≥80% (project standard) |
| Pages added | 5-7 new pages (P3-P5) |
| Components added | 15-20 new components |

---

**Detail Per-Phase docs**: Xem các file `phase-N-*/PLAN-phase-N.md` tương ứng.
