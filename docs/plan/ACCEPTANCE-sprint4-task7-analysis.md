# Sprint 4+ Task Group 7: Deep Analysis - Acceptance Criteria

## Definition of Done

---

## AC1: API Routes

- [ ] **AC1.1:** `GET /api/analysis/[id]` returns 14 outputs
- [ ] **AC1.2:** `POST /api/analysis/[id]` triggers job
- [ ] **AC1.3:** JWT enforced
- [ ] **AC1.4:** RLS: user A cannot see user B's analysis

---

## AC2: Main Page

- [ ] **AC2.1:** `/analysis/[id]` renders
- [ ] **AC2.2:** Empty state if not analyzed
- [ ] **AC2.3:** Tabs work (6 tabs)
- [ ] **AC2.4:** Re-analyze button charges 50 credits
- [ ] **AC2.5:** Back button returns to assistant

---

## AC3: 6 Tabs

- [ ] **AC3.1:** Overview tab shows summary cards
- [ ] **AC3.2:** Deterministic tab: Outputs 1-4
- [ ] **AC3.3:** NLP tab: Outputs 5-7
- [ ] **AC3.4:** LLM tab: Outputs 8-11 (with cost badges)
- [ ] **AC3.5:** Insights tab: Outputs 12-13
- [ ] **AC3.6:** Thumbnail tab: Output 14

---

## AC4: Components

- [ ] **AC4.1:** OutputCard reusable
- [ ] **AC4.2:** JsonViewer expandable
- [ ] **AC4.3:** ReanalyzeButton confirm dialog
- [ ] **AC4.4:** Loading states
- [ ] **AC4.5:** Error states

---

## AC5: Cache Behavior

- [ ] **AC5.1:** First load shows existing data
- [ ] **AC5.2:** Re-analyze within 24h shows warning
- [ ] **AC5.3:** After re-analyze, version increments

---

## AC6: RLS & Security

- [ ] **AC6.1:** User A cannot fetch user B's analysis
- [ ] **AC6.2:** Direct POST without ownership → 403
- [ ] **AC6.3:** No JWT → 401

---

## AC7: Code Quality

- [ ] **AC7.1:** TypeScript strict
- [ ] **AC7.2:** Component reuse
- [ ] **AC7.3:** `pnpm lint` passes

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] 14 outputs visible
3. [ ] Tabs navigate correctly
4. [ ] RLS verified

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 7 - Deep Analysis
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/analysis/[assistant_id]/page.tsx
  - apps/web/app/api/analysis/[assistant_id]/route.ts
  - apps/web/components/analysis/* (10 components)
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Idea Generation
```