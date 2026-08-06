import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { CreditsCard } from '@/components/credits-card';
import { PricingTable } from '@/components/pricing-table';
import { TransactionHistory } from '@/components/transaction-history';
import { IconBilling } from '@/components/icons';

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

  const totalUsed = Math.abs(
    transactions
      .filter((t: any) => t.amount < 0 && t.metadata?.status !== 'refunded')
      .reduce((sum: number, t: any) => sum + t.amount, 0)
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-up">
      <div className="space-y-3 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          <IconBilling size={14} /> Billing
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Billing &amp; Credits</span>
        </h1>
        <p className="text-[var(--fg-secondary)] max-w-md mx-auto">
          Theo dõi credits, plan và lịch sử giao dịch của tài khoản.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        <CreditsCard
          credits={balance.credits}
          tier={balance.tier}
          monthlyQuota={monthlyQuota}
          lastTopup={lastTopup}
        />

        <div className="relative glass-strong rounded-2xl p-6 overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-16 -right-16 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
          />
          <div className="relative space-y-2">
            <p className="text-sm text-[var(--fg-secondary)]">Tier hiện tại</p>
            <p className="text-4xl font-bold gradient-text uppercase tracking-tight">
              {balance.tier}
            </p>
            <p className="text-xs text-[var(--fg-tertiary)]">
              {monthlyQuota.toLocaleString('vi-VN')} credits/tháng
            </p>
          </div>
        </div>

        <div className="relative glass-strong rounded-2xl p-6 overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-16 -right-16 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
          />
          <div className="relative space-y-2">
            <p className="text-sm text-[var(--fg-secondary)]">Tổng đã dùng</p>
            <p className="text-4xl font-bold text-white">
              {totalUsed.toLocaleString('vi-VN')}
            </p>
            <p className="text-xs text-[var(--fg-tertiary)]">credits đã tiêu</p>
          </div>
        </div>
      </div>

      <PricingTable pricing={pricing} />

      <TransactionHistory transactions={transactions} />
    </div>
  );
}