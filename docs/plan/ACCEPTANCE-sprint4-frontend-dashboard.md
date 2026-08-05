# Sprint 4 Task Group 4: Frontend Dashboard - Acceptance Criteria

## Definition of Done

---

## AC1: Dashboard

- [ ] **AC1.1:** `/dashboard` renders
- [ ] **AC1.2:** Shows recent jobs
- [ ] **AC1.3:** Job cards link to detail
- [ ] **AC1.4:** Auth check (redirect if not logged in)

---

## AC2: New Project

- [ ] **AC2.1:** `/projects/new` has URL form
- [ ] **AC2.2:** Submits to `/api/channels/collect`
- [ ] **AC2.3:** Redirects to `/jobs/[id]` on success
- [ ] **AC2.4:** Shows error on failure

---

## AC3: Job Progress

- [ ] **AC3.1:** `/jobs/[id]` renders
- [ ] **AC3.2:** Shows overall progress
- [ ] **AC3.3:** Subscribes to Supabase Realtime
- [ ] **AC3.4:** Updates without refresh
- [ ] **AC3.5:** Shows sub-progress (14 outputs)

---

## AC4: Script Editor

- [ ] **AC4.1:** `/scripts/[id]` renders
- [ ] **AC4.2:** Editable hook/body/cta
- [ ] **AC4.3:** Scene timeline with B-roll
- [ ] **AC4.4:** Timestamps formatted

---

## AC5: Realtime

- [ ] **AC5.1:** Supabase Realtime working
- [ ] **AC5.2:** Channel cleanup on unmount
- [ ] **AC5.3:** No hydration errors

---

## AC6: Code Quality

- [ ] **AC6.1:** TypeScript strict
- [ ] **AC6.2:** Components reusable
- [ ] **AC6.3:** `pnpm lint` passes
- [ ] **AC6.4:** `pnpm type-check` passes

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] `pnpm dev` works
3. [ ] Realtime updates without refresh

---

## Sign-off

```
✓ Task: Sprint 4 - Frontend Dashboard
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/dashboard/page.tsx
  - apps/web/app/projects/new/page.tsx
  - apps/web/app/jobs/[id]/page.tsx
  - apps/web/app/scripts/[id]/page.tsx
  - apps/web/components/job-card.tsx
  - apps/web/components/sub-progress-list.tsx
  - apps/web/components/scene-timeline.tsx
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Integration
```
