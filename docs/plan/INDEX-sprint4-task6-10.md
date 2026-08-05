# Sprint 4+ - Task Groups 6-10 Index

## Overview

5 Task Groups bổ sung để hoàn thiện UI 100% flow:

| # | Task Group | Pages | Components | API Routes |
|---|------------|-------|-----------|-----------|
| 6 | Channel Assistants | 2 | 2 | 2 |
| 7 | Deep Analysis (14 outputs) | 1 | 10 | 1 |
| 8 | Idea Generation | 1 | 5 | 1 |
| 9 | Billing & Credits | 1 | 5 | 0 (đã có) |
| 10 | Account Settings & Pricing | 2 | 3 | 2 |
| **Total** | | **7 pages** | **25 components** | **6 routes** |

---

## Task Group Details

### Task Group 6: Channel Assistants

```
docs/plan/CONTEXT-sprint4-task6-assistants.md
docs/plan/SKILL-ROUTING-sprint4-task6-assistants.md
docs/plan/PLAN-sprint4-task6-assistants.md
docs/plan/MSEW-sprint4-task6-assistants.md
docs/plan/ACCEPTANCE-sprint4-task6-assistants.md
```

**Pages:** `/assistants`, `/assistants/[id]`

### Task Group 7: Deep Analysis

```
docs/plan/CONTEXT-sprint4-task7-analysis.md
docs/plan/SKILL-ROUTING-sprint4-task7-analysis.md
docs/plan/PLAN-sprint4-task7-analysis.md
docs/plan/MSEW-sprint4-task7-analysis.md
docs/plan/ACCEPTANCE-sprint4-task7-analysis.md
```

**Pages:** `/analysis/[assistant_id]`
**Tabs:** Overview, Deterministic, NLP, LLM, Insights, Thumbnail

### Task Group 8: Idea Generation

```
docs/plan/CONTEXT-sprint4-task8-ideas.md
docs/plan/SKILL-ROUTING-sprint4-task8-ideas.md
docs/plan/PLAN-sprint4-task8-ideas.md
docs/plan/MSEW-sprint4-task8-ideas.md
docs/plan/ACCEPTANCE-sprint4-task8-ideas.md
```

**Pages:** `/ideas/[assistant_id]`

### Task Group 9: Billing & Credits

```
docs/plan/CONTEXT-sprint4-task9-billing.md
docs/plan/SKILL-ROUTING-sprint4-task9-billing.md
docs/plan/PLAN-sprint4-task9-billing.md
docs/plan/MSEW-sprint4-task9-billing.md
docs/plan/ACCEPTANCE-sprint4-task9-billing.md
```

**Pages:** `/billing`
**Header widget:** CreditsBadge

### Task Group 10: Account Settings

```
docs/plan/CONTEXT-sprint4-task10-account.md
docs/plan/SKILL-ROUTING-sprint4-task10-account.md
docs/plan/PLAN-sprint4-task10-account.md
docs/plan/MSEW-sprint4-task10-account.md
docs/plan/ACCEPTANCE-sprint4-task10-account.md
```

**Pages:** `/account/settings`, `/pricing`

---

## Final UI Flow (Complete)

```
Login/Register
    │
    ▼
Dashboard ──── Credits Badge (header)
    │
    ├── /assistants ── Channel DNA list
    │      │
    │      ▼
    │   /assistants/[id] ── 4 action buttons
    │      │
    │      ├── /analysis/[id] ── 14 outputs
    │      │       │
    │      │       └── Re-analyze (50c)
    │      │
    │      ├── /ideas/[id] ── Gap score ideas
    │      │       │
    │      │       └── "Tạo Script" → /jobs/[id]
    │      │
    │      └── /scripts/[id] ── Editor (existing)
    │
    ├── /billing ── Balance + History + Pricing
    │
    ├── /account/settings ── Profile + Password
    │
    └── /pricing ── Tier comparison
```

---

## Files Summary (Total: 50+ files)

### Pages (10 mới)
- `/assistants/page.tsx`
- `/assistants/[id]/page.tsx`
- `/analysis/[assistant_id]/page.tsx`
- `/ideas/[assistant_id]/page.tsx`
- `/billing/page.tsx`
- `/account/settings/page.tsx`
- `/pricing/page.tsx`

### Components (25 mới)

#### Assistants (2)
- `assistant-card.tsx`
- `assistant-actions.tsx`

#### Analysis (10)
- `analysis-tabs.tsx`
- `overview-tab.tsx`
- `deterministic-tab.tsx`
- `nlp-tab.tsx`
- `llm-tab.tsx`
- `insights-tab.tsx`
- `thumbnail-tab.tsx`
- `output-card.tsx`
- `json-viewer.tsx`
- `reanalyze-button.tsx`

#### Ideas (5)
- `idea-card.tsx`
- `idea-filters.tsx`
- `regenerate-button.tsx`
- `ideas-list.tsx`
- `gap-score-badge.tsx` (trong idea-card)

#### Billing (5)
- `credits-badge.tsx`
- `credits-card.tsx`
- `pricing-table.tsx`
- `transaction-history.tsx`
- `usage-stats-card.tsx` (inline trong page)

#### Account (3)
- `profile-form.tsx`
- `password-form.tsx`
- `pricing-card.tsx`

### API Routes (6 mới)
- `api/assistants/route.ts`
- `api/assistants/[id]/route.ts`
- `api/analysis/[assistant_id]/route.ts`
- `api/ideas/[assistant_id]/route.ts`
- `api/account/update-profile/route.ts`
- `api/account/change-password/route.ts`

---

## Backend API Cần Bổ Sung (Task 11+)

⚠️ **Lưu ý quan trọng:** Các Task Groups 6-10 giả định backend có các endpoints:

| Endpoint | Status | Note |
|----------|--------|------|
| `GET /api/assistants` | ❌ Cần tạo | List user's assistants |
| `GET /api/assistants/[id]` | ❌ Cần tạo | Get single |
| `DELETE /api/assistants/[id]` | ❌ Cần tạo | Delete |
| `GET /api/analysis/[assistant_id]` | ❌ Cần tạo | Get 14 outputs |
| `POST /api/analysis/[assistant_id]/reanalyze` | ❌ Cần tạo | Trigger analysis |
| `GET /api/ideas/[assistant_id]` | ❌ Cần tạo | Get ideas |
| `GET /api/credits/pricing` | ❌ Cần tạo | Get pricing |
| `POST /api/jobs/trigger` | ❌ Cần tạo | Generic job trigger |

→ Nên có **Task Group 11: Backend API Completion** để build các endpoint trên.

---

## Estimated Timeline

| Task Group | Effort | Frontend | Backend |
|------------|--------|----------|---------|
| 6: Assistants | 8h | 6h | 2h |
| 7: Analysis | 12h | 10h | 2h |
| 8: Ideas | 6h | 5h | 1h |
| 9: Billing | 6h | 6h | 0h |
| 10: Account | 6h | 6h | 0h |
| **Total** | **38h** | **33h** | **5h** |

---

## Next Steps

1. Tier 2 implement Task Groups 6-10 theo thứ tự (vì có dependencies)
2. Hoặc implement song song với Task Group 11 (Backend API)
3. Sau khi xong → E2E tests + production-ready