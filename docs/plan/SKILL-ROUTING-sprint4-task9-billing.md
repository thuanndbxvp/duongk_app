# Sprint 4+ Task Group 9: Billing & Credits - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (apps/web only)
- ✅ ReadLints

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Backend (CreditManager)
- ❌ Đổi Tasks 1-8 code
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Server-Side Initial Fetch

```typescript
// page.tsx - Server Component
export default async function BillingPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const [balance, transactions, pricing] = await Promise.all([
    fetchBalance(token),
    fetchTransactions(token),
    fetchPricing(token),
  ]);

  return <BillingView balance={balance} transactions={transactions} pricing={pricing} />;
}
```

### 2. Credits Badge in Layout

```typescript
// components/credits-badge.tsx
'use client';
import { useEffect, useState } from 'react';

export function CreditsBadge() {
  const [credits, setCredits] = useState<number | null>(null);
  
  useEffect(() => {
    fetch('/api/credits/balance')
      .then(r => r.json())
      .then(d => setCredits(d.credits));
  }, []);
  
  if (credits === null) return null;
  if (credits < 20) return <span className="bg-red-500">⚠️ {credits}</span>;
  return <span className="bg-green-500">{credits}</span>;
}
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/app/billing/page.tsx`
- ✅ `apps/web/components/credits-badge.tsx`
- ✅ `apps/web/components/credits-card.tsx`
- ✅ `apps/web/components/pricing-table.tsx`
- ✅ `apps/web/components/transaction-history.tsx`

## Files KHÔNG ĐƯỢC SỬA
- ❌ `apps/api/routers/credits.py` (đã có)
- ❌ `apps/api/services/credit_manager.py`
- ❌ `apps/web/components/*` (Tasks 6-8)