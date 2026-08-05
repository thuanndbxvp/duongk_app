# Sprint 4+ Task Group 9: Billing & Credits UI

## 1. Context & Mục đích

### Bối cảnh

Backend đã có:
- `CreditManager` (hold/adjust/commit/refund)
- `/api/credits/balance` endpoint
- `/api/credits/transactions` endpoint
- `credit_pricing` table (7 job types)
- `users.credits` và `users.tier`

UI hiện tại **KHÔNG CÓ**:
- Credits badge ở header
- `/billing` page
- Transaction history
- Credit purchase flow
- Usage analytics

### Mục đích task group này

- **`/billing` page** với:
  - Balance card (current credits)
  - Tier info
  - Transaction history table
  - Pricing breakdown per job type
- **Credits badge** ở dashboard header (always visible)
- **Low credits warning** khi < 20 credits

### Phụ thuộc

- ✅ Task 1: User & RLS
- ✅ Task 2: BFF
- ✅ Task 3: Credit System
- ✅ Backend `/api/credits/*` đã có

---

## 2. UI Layout

### `/billing`

```
┌─────────────────────────────────────────────────────────────────────┐
│  Billing & Credits                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │ 87 credits      │ │ Tier: PRO       │ │ Last topup:     │       │
│  │ còn lại         │ │ 500 credits/mo  │ │ 2026-07-15      │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│                                                                      │
│  [+ Nạp thêm credits] (mock for now)                              │
│                                                                      │
│  Pricing per operation:                                              │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ Niche Validate      5 credits                            │       │
│  │ Collect Channel    10 credits                            │       │
│  │ Deep Analysis      50 credits                            │       │
│  │ Idea Generation     5 credits                            │       │
│  │ Generate Script    30 credits                            │       │
│  │ Scene Breakdown    10 credits                            │       │
│  │ RAG Retrieve        1 credit                             │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                      │
│  Transaction History:                                                │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ Date         Type           Amount    Balance    Status │       │
│  │ 2026-08-05   script_gen     -30       87         ✓ done │       │
│  │ 2026-08-04   deep_analysis  -50       117        ✓ done │       │
│  │ 2026-08-03   collect        -10       167        ✓ done │       │
│  │ 2026-08-01   topup          +500      177        ✓ done │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/billing/page.tsx` | Main billing page |
| `apps/web/components/credits-badge.tsx` | Header badge |
| `apps/web/components/credits-card.tsx` | Balance card |
| `apps/web/components/pricing-table.tsx` | Pricing list |
| `apps/web/components/transaction-history.tsx` | History table |

---

## 4. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | /billing page renders |
| AC2 | Show balance + tier |
| AC3 | Pricing table correct |
| AC4 | Transaction history list |
| AC5 | Credits badge in header |
| AC6 | Low credits warning |
| AC7 | Empty transactions state |
| AC8 | RLS isolation |