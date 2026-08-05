# Sprint 4+ Task Group 9: Billing & Credits - Acceptance Criteria

## Definition of Done

---

## AC1: Main Page

- [ ] **AC1.1:** `/billing` renders
- [ ] **AC1.2:** Shows balance card
- [ ] **AC1.3:** Shows tier info
- [ ] **AC1.4:** Shows total used
- [ ] **AC1.5:** Empty transactions state

---

## AC2: CreditsBadge

- [ ] **AC2.1:** Shows in header
- [ ] **AC2.2:** Auto-refreshes every 30s
- [ ] **AC2.3:** Red color when < 20
- [ ] **AC2.4:** Green color when ≥ 20
- [ ] **AC2.5:** Click → /billing

---

## AC3: PricingTable

- [ ] **AC3.1:** Shows 7 job types
- [ ] **AC3.2:** Credits amount correct
- [ ] **AC3.3:** Description visible

---

## AC4: TransactionHistory

- [ ] **AC4.1:** Shows date/type/amount/status
- [ ] **AC4.2:** Color coding (green=refund, red=charge)
- [ ] **AC4.3:** Status badges
- [ ] **AC4.4:** Empty state

---

## AC5: RLS

- [ ] **AC5.1:** User A cannot see user B's transactions
- [ ] **AC5.2:** Balance reflects correct user

---

## AC6: Code Quality

- [ ] **AC6.1:** TypeScript strict
- [ ] **AC6.2:** Loading states
- [ ] **AC6.3:** Error handling

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] CreditsBadge works in header
3. [ ] Pricing table visible

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 9 - Billing & Credits
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/billing/page.tsx
  - apps/web/components/credits-badge.tsx
  - apps/web/components/credits-card.tsx
  - apps/web/components/pricing-table.tsx
  - apps/web/components/transaction-history.tsx
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Account Settings
```