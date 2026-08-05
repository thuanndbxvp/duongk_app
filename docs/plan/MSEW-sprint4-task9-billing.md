# Sprint 4+ Task Group 9: Billing & Credits - MSEW

## Checklist

- [ ] Bước 1: CreditsBadge component
- [ ] Bước 2: CreditsCard component
- [ ] Bước 3: PricingTable component
- [ ] Bước 4: TransactionHistory component
- [ ] Bước 5: Main billing page
- [ ] Bước 6: Add CreditsBadge to layout
- [ ] Bước 7: Verify

---

## Bước 1: CreditsBadge (Header widget)

**File:** `apps/web/components/credits-badge.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export function CreditsBadge() {
  const [credits, setCredits] = useState<number | null>(null);
  const [tier, setTier] = useState<string>('free');

  useEffect(() => {
    async function fetchBalance() {
      try {
        const res = await fetch('/api/credits/balance');
        if (res.ok) {
          const data = await res.json();
          setCredits(data.credits);
          setTier(data.tier);
        }
      } catch (e) {
        // Silent fail - badge hidden if can't fetch
      }
    }
    fetchBalance();
    // Refresh every 30s
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  if (credits === null) return null;

  const isLow = credits < 20;
  const colorClass = isLow
    ? 'bg-red-100 text-red-800 border-red-300'
    : 'bg-green-100 text-green-800 border-green-300';

  return (
    <Link
      href="/billing"
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClass} hover:shadow transition-shadow text-sm font-medium`}
    >
      <span>💰</span>
      <span>{credits} credits</span>
      <span className="text-xs opacity-70">({tier})</span>
      {isLow && <span>⚠️</span>}
    </Link>
  );
}
```

---

## Bước 2: CreditsCard

**File:** `apps/web/components/credits-card.tsx`

```typescript
interface Props {
  credits: number;
  tier: string;
  monthlyQuota?: number;
  lastTopup?: string;
}

export function CreditsCard({ credits, tier, monthlyQuota, lastTopup }: Props) {
  const isLow = credits < 20;
  const percentage = monthlyQuota
    ? Math.round((credits / monthlyQuota) * 100)
    : null;

  return (
    <div className={`bg-white rounded-lg shadow border-l-4 p-6 ${
      isLow ? 'border-red-500' : 'border-green-500'
    }`}>
      <p className="text-sm text-gray-500">Credits còn lại</p>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-4xl font-bold">{credits}</span>
        <span className="text-sm text-gray-500">
          {monthlyQuota ? `/ ${monthlyQuota}` : ''}
        </span>
      </div>
      {percentage !== null && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                percentage < 20 ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, percentage)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{percentage}% còn lại</p>
        </div>
      )}
      {isLow && (
        <p className="text-xs text-red-600 mt-2">⚠️ Sắp hết credits</p>
      )}
    </div>
  );
}
```

---

## Bước 3: PricingTable

**File:** `apps/web/components/pricing-table.tsx`

```typescript
interface PricingItem {
  job_type: string;
  credits: number;
  description: string;
}

const DEFAULT_PRICING: PricingItem[] = [
  { job_type: 'niche_validate', credits: 5, description: 'Validate a YouTube niche' },
  { job_type: 'collect_channel', credits: 10, description: 'Collect metadata + transcripts' },
  { job_type: 'deep_analysis', credits: 50, description: 'Run 14-output deep analysis' },
  { job_type: 'idea_generation', credits: 5, description: 'Generate HDBSCAN-based ideas' },
  { job_type: 'script_generation', credits: 30, description: 'Generate AI script with RAG' },
  { job_type: 'scene_breakdown', credits: 10, description: 'Break script into scenes with B-roll' },
  { job_type: 'rag_retrieve', credits: 1, description: 'RAG context retrieval' },
];

export function PricingTable({ pricing }: { pricing?: PricingItem[] }) {
  const items = pricing || DEFAULT_PRICING;

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="p-6 border-b">
        <h2 className="text-xl font-bold">Pricing per Operation</h2>
        <p className="text-sm text-gray-500 mt-1">
          Credits bị trừ mỗi khi chạy job
        </p>
      </div>
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Operation
            </th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Description
            </th>
            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">
              Credits
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => (
            <tr key={item.job_type} className="hover:bg-gray-50">
              <td className="px-6 py-4 font-mono text-sm">{item.job_type}</td>
              <td className="px-6 py-4 text-sm text-gray-600">
                {item.description}
              </td>
              <td className="px-6 py-4 text-right">
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold text-sm">
                  {item.credits}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Bước 4: TransactionHistory

**File:** `apps/web/components/transaction-history.tsx`

```typescript
interface Transaction {
  id: string;
  amount: number;  // negative = charge, positive = refund/topup
  job_type?: string;
  metadata?: any;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  committed: 'bg-green-100 text-green-800',
  refunded: 'bg-blue-100 text-blue-800',
  done: 'bg-green-100 text-green-800',
};

export function TransactionHistory({
  transactions,
}: {
  transactions: Transaction[];
}) {
  if (transactions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow border p-8 text-center">
        <p className="text-gray-500">Chưa có giao dịch nào.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="p-6 border-b">
        <h2 className="text-xl font-bold">Transaction History</h2>
        <p className="text-sm text-gray-500 mt-1">
          {transactions.length} giao dịch gần nhất
        </p>
      </div>
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Date
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Type
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">
              Amount
            </th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {transactions.map((tx) => {
            const status = tx.metadata?.status || 'done';
            const typeLabel =
              tx.job_type || (tx.amount > 0 ? 'topup' : 'unknown');

            return (
              <tr key={tx.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  {new Date(tx.created_at).toLocaleString('vi-VN')}
                </td>
                <td className="px-4 py-3 text-sm font-mono">{typeLabel}</td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={`font-bold ${
                      tx.amount > 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {tx.amount > 0 ? '+' : ''}
                    {tx.amount}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      STATUS_COLORS[status] || 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Bước 5: Main Billing Page

**File:** `apps/web/app/billing/page.tsx`

```typescript
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { CreditsCard } from '@/components/credits-card';
import { PricingTable } from '@/components/pricing-table';
import { TransactionHistory } from '@/components/transaction-history';

const TIER_QUOTAS: Record<string, number> = {
  free: 100,
  pro: 500,
  enterprise: 5000,
};

export default async function BillingPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  // Parallel fetch
  const [balanceRes, txRes, pricingRes] = await Promise.all([
    apiFetch('/api/credits/balance', {}, token),
    apiFetch('/api/credits/transactions', {}, token),
    apiFetch('/api/credits/pricing', {}, token).catch(() => null),
  ]);

  const balance = balanceRes.ok ? await balanceRes.json() : { credits: 0, tier: 'free' };
  const transactions = txRes.ok ? await txRes.json() : [];
  const pricing = pricingRes?.ok ? await pricingRes.json() : null;

  const monthlyQuota = TIER_QUOTAS[balance.tier] || 100;
  const lastTopup = transactions.find((t: any) => t.amount > 0)?.created_at;

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-8">Billing & Credits</h1>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <CreditsCard
          credits={balance.credits}
          tier={balance.tier}
          monthlyQuota={monthlyQuota}
          lastTopup={lastTopup}
        />
        <div className="bg-white rounded-lg shadow border p-6">
          <p className="text-sm text-gray-500">Tier hiện tại</p>
          <p className="text-3xl font-bold mt-1 uppercase">
            {balance.tier}
          </p>
          <p className="text-xs text-gray-500 mt-2">
            {monthlyQuota} credits/tháng
          </p>
        </div>
        <div className="bg-white rounded-lg shadow border p-6">
          <p className="text-sm text-gray-500">Tổng đã dùng</p>
          <p className="text-3xl font-bold mt-1">
            {Math.abs(
              transactions
                .filter((t: any) => t.amount < 0 && t.metadata?.status !== 'refunded')
                .reduce((sum: number, t: any) => sum + t.amount, 0)
            )}
          </p>
          <p className="text-xs text-gray-500 mt-2">credits</p>
        </div>
      </div>

      <div className="mb-8">
        <PricingTable pricing={pricing} />
      </div>

      <TransactionHistory transactions={transactions} />
    </main>
  );
}
```

---

## Bước 6: Add Badge to Layout

**File:** `apps/web/app/layout.tsx` (update)

```typescript
import { CreditsBadge } from '@/components/credits-badge';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <header className="border-b bg-white">
          <div className="container mx-auto px-8 py-4 flex items-center justify-between">
            <a href="/" className="font-bold text-xl">AppDK</a>
            <CreditsBadge />
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
```

---

## Bước 7: Verify

```bash
cd apps/web
pnpm dev
# Navigate http://localhost:3000/billing
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task9-billing.md
cat docs/plan/SKILL-ROUTING-sprint4-task9-billing.md
cat docs/plan/PLAN-sprint4-task9-billing.md
cat docs/plan/MSEW-sprint4-task9-billing.md
cat docs/plan/ACCEPTANCE-sprint4-task9-billing.md
```