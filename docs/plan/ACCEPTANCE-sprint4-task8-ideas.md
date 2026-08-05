# Sprint 4+ Task Group 8: Idea Generation - Acceptance Criteria

## Definition of Done

---

## AC1: API Routes

- [ ] **AC1.1:** `GET /api/ideas/[id]` returns list
- [ ] **AC1.2:** JWT enforced
- [ ] **AC1.3:** Returns empty array if no ideas
- [ ] **AC1.4:** Sorted by gap_score DESC

---

## AC2: Main Page

- [ ] **AC2.1:** `/ideas/[id]` renders
- [ ] **AC2.2:** Shows stats (total/top/avg/high)
- [ ] **AC2.3:** Empty state
- [ ] **AC2.4:** Regenerate button works
- [ ] **AC2.5:** Back button returns

---

## AC3: IdeaCard

- [ ] **AC3.1:** Shows topic name
- [ ] **AC3.2:** Gap score with color (green/yellow/red)
- [ ] **AC3.3:** Confidence badge
- [ ] **AC3.4:** Cluster id
- [ ] **AC3.5:** Related topics as chips
- [ ] **AC3.6:** Opportunity description highlighted
- [ ] **AC3.7:** "Tạo Script" button → triggers job

---

## AC4: Filters

- [ ] **AC4.1:** Search by topic works
- [ ] **AC4.2:** Filter by confidence works
- [ ] **AC4.3:** Sort by gap score
- [ ] **AC4.4:** Sort by alphabet
- [ ] **AC4.5:** Filter + sort combine correctly

---

## AC5: Regenerate Flow

- [ ] **AC5.1:** Confirm dialog before charge
- [ ] **AC5.2:** Triggers job
- [ ] **AC5.3:** Redirects to /jobs/[id]
- [ ] **AC5.4:** Insufficient credits → 402

---

## AC6: RLS

- [ ] **AC6.1:** User A cannot see user B's ideas
- [ ] **AC6.2:** Direct API call filtered

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] Filters work client-side
3. [ ] Script generation triggered

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 8 - Idea Generation
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/ideas/[assistant_id]/page.tsx
  - apps/web/app/api/ideas/[assistant_id]/route.ts
  - apps/web/components/ideas/idea-card.tsx
  - apps/web/components/ideas/idea-filters.tsx
  - apps/web/components/ideas/regenerate-button.tsx
  - apps/web/components/ideas/ideas-list.tsx
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Billing & Credits
```