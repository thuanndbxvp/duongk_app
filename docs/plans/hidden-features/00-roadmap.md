# Hidden Features Roadmap — Master Document

> **Tổng quan toàn bộ 6 phases để wire UI cho hidden features**
> **Ngày**: 2026-08-07
> **Status**: Phase 1-6 docs ready
> **Tier**: 1 (planning)

---

## 1. Background

Tier 1 audit ngày 2026-08-07 (`docs/HIDDEN-FEATURES-GAP-ANALYSIS.md`) phát hiện:
- **~45 backend endpoints** đã code nhưng không có UI access
- **~16 DB tables** có fields không được display/edit
- **6 service files** không ai import
- **12 endpoint drift** giữa FE call vs BE route

## 2. Phân chia phase

| Phase | Tên | Effort | Risk | Focus |
|---|---|---|---|---|
| **P1** | Quick Wins | 2 ngày | LOW | Drift fixes, cancel render, cleanup |
| **P2** | Wire Existing | 3 ngày | LOW | Analysis tabs + script regen |
| **P3** | Voice Profiles | 4 ngày | MED | New page |
| **P4** | Style Bible UI | 5 ngày | MED | New multi-section page |
| **P5** | Asset + Channel | 4 ngày | MED | 2 new pages |
| **P6** | Admin + Cleanup | 3 ngày | LOW | Admin tools + DB cleanup |

**Total**: 21 ngày (~3 tuần)

## 3. Dependency graph

```
P1 (foundation) ──> P2 (wire existing)
                ──> P3 (voice profiles)
                ──> P5 (asset + channel)
                ──> P6 (admin + cleanup)
P2 ──> P4 (style bible, cần analysis tabs)
```

## 4. Mapping audit → phase

| Audit finding | Phase |
|---|---|
| §3.2 — Endpoint drift (12 cases) | P1 |
| §3.1.F — Cancel render job | P1 |
| §5.1 — Dead services (6 files) | P1 |
| §5.1 — config_watcher not started | P1 |
| §3.1.A — Analysis tabs not wired | P2 |
| §3.1.G — Script regenerate/versions | P2 |
| §3.1.B — Voice profiles | P3 |
| §3.1.C — Style bible | P4 |
| §3.1.D — Asset library | P5 |
| §3.1.E — Channel collector | P5 |
| §3.1.F — Admin backup, traffic, users | P6 |
| §4.B — DB columns unused | P6 |

## 5. Definition of success

- [ ] Zero orphan endpoints (Phase 1-3)
- [ ] All admin tools accessible via UI (Phase 6)
- [ ] DB schema clean (Phase 6)
- [ ] Test coverage ≥80% across all phases
- [ ] No new P0/P1 bugs introduced

## 6. Risk mitigation

| Risk | Mitigation |
|---|---|
| Phase 1 drift fixes break other features | Full E2E test before merge |
| Phase 3 multipart upload issues | Test với file lớn, multiple formats |
| Phase 4 style bible scope creep | Strict MVP scope, defer advanced features |
| Phase 5 channel scraping timeout | Polling design OK, WebSocket later |
| Phase 6 DB migration data loss | Backup first, staged rollout |

## 7. Open questions

1. **Voice profile vs system voice**: Tier 2 nên ẩn system voice hay cho user switch?
   → Tier 1 default: hiển thị cả hai, label rõ ràng.

2. **Channel collector rate limit**: Backend có rate limit không?
   → Tier 2 verify trong P5 execution. Có thể cần add rate limit UI.

3. **Admin backup encryption**: Backup JSON plaintext hay encrypted?
   → Tier 1 default: plaintext. Add encryption trong Phase 7.

4. **DB column drops vs add UI**: Khi nào drop vs add UI?
   → Tier 2 chọn per-column dựa trên business value.

## 8. Tier 2 execution plan

Tier 2 thực hiện theo sequence:
1. Đọc `phase-N-{name}/PLAN-phase-N.md`
2. Đọc `phase-N-{name}/ACCEPTANCE-phase-N.md`
3. Implement theo `MSEW-phase-N.md` warnings
4. Self-review bằng `AUDIT-REPORT-phase-N.md` checklist
5. Submit → Tier 1 review → merge

## 9. References

- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` — Source audit
- `docs/plans/20260807-0305-zero-to-video-evolution/` — Previous phases
- `docs/operations/release-gates.md` — Launch criteria