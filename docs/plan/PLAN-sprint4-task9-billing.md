# Sprint 4+ Task Group 9: Billing & Credits - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  BILLING FLOW                                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → /billing                                                 │
│     │                                                            │
│     ▼                                                            │
│  Server fetch (3 parallel calls):                                │
│     ├── GET /api/credits/balance                                │
│     ├── GET /api/credits/transactions                           │
│     └── GET /api/credits/pricing                                │
│                                                                   │
│     ▼                                                            │
│  UI: Balance + Pricing + History                                │
│                                                                   │
│  Header: CreditsBadge shows current balance                     │
│     │                                                            │
│     ▼ (if < 20)                                                 │
│  Warning banner: "Sắp hết credits"                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Files to Create

### 1. Main Page

- `apps/web/app/billing/page.tsx`

### 2. Components

- `apps/web/components/credits-badge.tsx` (header widget)
- `apps/web/components/credits-card.tsx` (balance card)
- `apps/web/components/pricing-table.tsx` (pricing list)
- `apps/web/components/transaction-history.tsx` (history table)

---

## Backend Reference

### Existing endpoints

```python
GET /api/credits/balance
# Returns: {credits: int, tier: str}

GET /api/credits/transactions
# Returns: List[{id, amount, job_type, metadata, created_at, ...}]

# CẦN THÊM (backend):
GET /api/credits/pricing
# Returns: List[{job_type, credits, description}]
```

---

## Constraints

1. **Server Component** initial render (no loading flicker)
2. **Currency formatting** (USD for cost tracking)
3. **Date formatting** (vi-VN locale)
4. **Pagination** for transactions (50 limit)
5. **Empty states** (no transactions)
6. **Low credits alert** at 20 or below