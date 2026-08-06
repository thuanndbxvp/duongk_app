# Roadmap Index — AppDK Audit → Admin Panel

> Planner: Tầng 1 (Cursor Assistant)
> Ngày tạo: 2026-08-06
> Dựa trên: `docs/audit/codebase_audit_report.md` + `docs/plans/admin_panel_plan.md`

## Tổng quan
Audit Phần 1 phát hiện **9 issues chặn** (blockers) + **25 features** với tỉ lệ 🟢 36% / 🟡 52% / 🔴 12%. Admin Panel Phần 2 có 5 sprint A1-A5.
Để tránh Tier 2 làm tràn scope, tôi chia thành **10 phase**, mỗi phase có 5 file chuẩn (CONTEXT + SKILL-ROUTING + PLAN + MSEW + ACCEPTANCE).

## Thứ tự thực thi (Tier 2 cày theo thứ tự này)

### ✅ Phase 0 — Audit (ĐÃ HOÀN THÀNH)
- Output: `docs/audit/codebase_audit_report.md`
- Status: ✅ Done (2026-08-06)

### 📋 Phase 1 — Pre-flight blockers (ƯU TIÊN CAO)
Mục tiêu: Fix 4 issues chặn không cho phép admin test trên data thật.
- File outputs (sẽ tạo khi bắt đầu):
  - `docs/plan/CONTEXT-phase1-preflight-blockers.md`
  - `docs/plan/SKILL-ROUTING-phase1-preflight-blockers.md`
  - `docs/plan/PLAN-phase1-preflight-blockers.md`
  - `docs/plan/MSEW-phase1-preflight-blockers.md`
  - `docs/plan/ACCEPTANCE-phase1-preflight-blockers.md`
- Nội dung:
  - Step A: Cleanup duplicate `hold_credits` signature (SQL function ambiguity)
  - Step B: Fix RLS `transcripts` (scope theo assistant thay vì "all authenticated")
  - Step C: Thêm 7 endpoint FastAPI còn thiếu: `/api/assistants`, `/api/assistants/{id}`, `/api/jobs/trigger`, `/api/jobs/{id}`, `/api/analysis/{id}`, `/api/analysis/{id}/reanalyze`, `/api/ideas/{id}`, `/api/channels/collect`, `/api/credits/pricing`
  - Step D: Refactor `analysis_task.py` bỏ `fetch_mock_data`, dùng `module_2a.YouTubeCollector` thật + `transcript.TranscriptEngine`

### 📋 Phase 2 — UI Polish (nice-to-have, không chặn)
- CSS đồng bộ dark theme cho các trang legacy còn dùng `bg-white` (`/assistants/[id]`, `/analysis/[id]`, `/ideas/[id]`, `/jobs/[id]`, `/scripts/[id]`).

### 📋 Phase 3 — Env & Documentation
- Cập nhật `.env.example` đầy đủ (R2, MODAL, SUPADATA, SERPAPI, STALI).
- Cập nhật `.env.production.template` tương ứng.

### 📋 Phase 4 — Smoke Test & CI baseline
- Viết 1 script `scripts/smoke_test.ps1` để verify 40 routes của FastAPI có response.
- Setup GitHub Action đơn giản chạy pytest + smoke test.

### ✅ Phase 5 — Admin Foundation (FILE BÀN GIAO CHO TẦNG 2 NGAY)
**ĐÃ VIẾT XONG 5 FILE** (xem dưới).
- Tương ứng Sprint A1 trong `admin_panel_plan.md`.
- Nội dung: Migration 0022 + RBAC + Audit service + Middleware + AdminShell + Dashboard placeholder.

### 📋 Phase 6 — Admin Sprint A2 (User & Credit Management)
- Tương ứng Sprint A2: CRUD user + Adjust credit + Impersonate + Ledger view + Export CSV.

### 📋 Phase 7 — Admin Sprint A3 (API Key Management)
- Tương ứng Sprint A3: Vault wrapper + Key resolver + Cost tracking + Alert generator.

### 📋 Phase 8 — Admin Sprint A4 (Service Routing)
- Tương ứng Sprint A4: 8 features routing UI + Redis pub/sub hot-reload + Worker consumer.

### 📋 Phase 9 — Admin Sprint A5 (Polish)
- Tương ứng Sprint A5: Audit log viewer + Analytics + 2FA + Backup/restore + Admin handbook.

## File đã viết cho Phase 5 (sẵn sàng bàn giao Tier 2)

| # | File path | Purpose |
|---|-----------|---------|
| 1 | `docs/plan/CONTEXT-phase5-audit-fixes-foundation.md` | Bối cảnh + CodeGraph evidence |
| 2 | `docs/plan/SKILL-ROUTING-phase5-audit-fixes-foundation.md` | Bảng routing skill cho 12 step |
| 3 | `docs/plan/PLAN-phase5-audit-fixes-foundation.md` | Kiến trúc + rủi ro + effort |
| 4 | `docs/plan/MSEW-phase5-audit-fixes-foundation.md` | 12 micro-step với code snippet |
| 5 | `docs/plan/ACCEPTANCE-phase5-audit-fixes-foundation.md` | DoD + manual verify scripts |

## Lệnh copy cho Tier 2

Sếp copy lệnh này thả vào Terminal cho Tier 2 nó cày Phase 5 nhé:

```bash
/code phase5-audit-fixes-foundation
```

Sau khi Tier 2 xong, sẽ có file `docs/audit/AUDIT-REPORT-phase5-audit-fixes-foundation.md` theo template `AUDIT-REPORT.template.md`. Lúc đó Planner (Tôi) review rồi mới chuyển sang Phase 6.

## Ghi chú cho Tier 2
- Phase 5 là **foundation only**, không thêm feature nghiệp vụ admin nào.
- KHÔNG đụng `apps/api/routers/projects.py` (production).
- KHÔNG đụng `apps/api/modules/voice/*` (TTS production).
- KHÔNG đụng migrations 0001..0021.
- Mọi verify command đã viết PowerShell. Nếu Tier 2 dùng bash/cmd khác, phải adapt.

## Lý do chia phase theo thứ tự này
1. **Phase 1 trước Admin** vì admin test cần data thật (không test trên data mock → false positive).
2. **Phase 2-4 song song** với Phase 5 vì không phụ thuộc nhau (polish + docs + CI).
3. **Phase 5 → 9** theo đúng thứ tự Sprint A1-A5 trong plan admin (mỗi sprint 1 phase cho Tier 2 dễ cày).
