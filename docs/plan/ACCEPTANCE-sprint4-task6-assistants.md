# Sprint 4+ Task Group 6: Channel Assistants - Acceptance Criteria

## Definition of Done

---

## AC1: API Routes

- [ ] **AC1.1:** `GET /api/assistants` returns user's list
- [ ] **AC1.2:** `GET /api/assistants/[id]` returns single
- [ ] **AC1.3:** `DELETE /api/assistants/[id]` removes
- [ ] **AC1.4:** All require valid JWT
- [ ] **AC1.5:** Returns 401 if no token

### Test AC1:

```bash
# Without token
curl http://localhost:3000/api/assistants
# Expect: 401

# With token
curl -H "Authorization: Bearer <token>" http://localhost:3000/api/assistants
# Expect: 200 with array
```

---

## AC2: List Page

- [ ] **AC2.1:** `/assistants` renders
- [ ] **AC2.2:** Shows grid of cards
- [ ] **AC2.3:** Empty state when no assistants
- [ ] **AC2.4:** Each card has thumbnail + stats + status
- [ ] **AC2.5:** Click card → detail page

---

## AC3: AssistantCard Component

- [ ] **AC3.1:** Shows channel thumbnail
- [ ] **AC3.2:** Shows subscriber count (formatted)
- [ ] **AC3.3:** Shows video stats (total/viral/scripts)
- [ ] **AC3.4:** Shows status badge
- [ ] **AC3.5:** Shows "analyzed" badge if has_analysis
- [ ] **AC3.6:** Hover effect

---

## AC4: Detail Page

- [ ] **AC4.1:** `/assistants/[id]` renders
- [ ] **AC4.2:** Shows channel info card
- [ ] **AC4.3:** Shows 4 action buttons
- [ ] **AC4.4:** Buttons trigger correct jobs
- [ ] **AC4.5:** Shows recent jobs list
- [ ] **AC4.6:** Back button returns to list

---

## AC5: Action Buttons

- [ ] **AC5.1:** "Deep Analysis" triggers `deep_analysis` job
- [ ] **AC5.2:** "Generate Ideas" disabled if no analysis
- [ ] **AC5.3:** "Generate Script" disabled if no analysis
- [ ] **AC5.4:** "View Scripts" navigates to scripts page
- [ ] **AC5.5:** Loading state during API call
- [ ] **AC5.6:** Tooltip explains disabled buttons

---

## AC6: RLS Isolation

- [ ] **AC6.1:** User A cannot see User B's assistants
- [ ] **AC6.2:** Direct API call to other user's assistant → 404
- [ ] **AC6.3:** DELETE other user's assistant → 403

### Test AC6:

```python
def test_rls_isolation():
    # User1 creates assistant
    # User2 logs in
    # User2 GET /assistants → empty (RLS filter)
    # User2 GET /assistants/{user1_id} → 404
```

---

## AC7: Code Quality

- [ ] **AC7.1:** TypeScript strict
- [ ] **AC7.2:** Server Components cho default pages
- [ ] **AC7.3:** Client Components chỉ cho interactive
- [ ] **AC7.4:** No `any` types
- [ ] **AC7.5:** `pnpm lint` passes

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] `pnpm dev` works
3. [ ] RLS tests pass
4. [ ] No direct supabase calls

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 6 - Channel Assistants
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/assistants/page.tsx
  - apps/web/app/assistants/[id]/page.tsx
  - apps/web/app/api/assistants/route.ts
  - apps/web/app/api/assistants/[id]/route.ts
  - apps/web/components/assistant-card.tsx
  - apps/web/components/assistant-actions.tsx
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Deep Analysis Results
```