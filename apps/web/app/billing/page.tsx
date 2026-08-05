import { redirect } from 'next/navigation';
import { apiFetch } from '../../../lib/api-client';
import { getAccessToken } from '../../../lib/auth';
import { CreditsCard } from '../../../components/credits-card';
import { PricingTable } from '../../../components/pricing-table';
import { TransactionHistory } from '../../../components/transaction-history';

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
