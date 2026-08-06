'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useObjectFetch } from '@/lib/use-fetch';
import { IconUsers, IconChannels, IconBrain, IconShield } from '@/components/icons';

const Line = dynamic(() => import('react-chartjs-2').then(m => m.Line), { ssr: false });

interface DashboardStats {
  mrr_estimate_usd: number;
  active_users_24h: number;
  jobs_today: number;
  credits_spent_today: number;
  total_users: number;
  tier_breakdown: Record<string, { count: number; usd: number }>;
  generated_at: string;
}

export default function AdminDashboardPage() {
  const { data: stats } = useObjectFetch<DashboardStats>('/api/admin/dashboard/stats', []);
  const [revenueData, setRevenueData] = useState<any>(null);
  const [cohortData, setCohortData] = useState<any>(null);
  const [topCreators, setTopCreators] = useState<any>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  const fmt = new Intl.NumberFormat('en-US');
  const fmtUsd = (n: number) =>
    n === 0 ? '$0' : `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

  const statCards = [
    {
      label: 'MRR (estimate)',
      value: stats ? fmtUsd(stats.mrr_estimate_usd) : '—',
      hint: stats
        ? `${stats.total_users} users · ${Object.entries(stats.tier_breakdown).map(([t, v]) => `${t}=${v.count}`).join(' · ')}`
        : 'Sum tier pricing × active users',
      icon: IconChannels,
    },
    {
      label: 'Active Users (24h)',
      value: stats ? fmt.format(stats.active_users_24h) : '—',
      hint: 'Distinct users with jobs in 24h',
      icon: IconUsers,
    },
    {
      label: 'Jobs Today',
      value: stats ? fmt.format(stats.jobs_today) : '—',
      hint: 'Jobs created since 00:00 UTC',
      icon: IconBrain,
    },
    {
      label: 'Credits Spent Today',
      value: stats ? fmt.format(stats.credits_spent_today) : '—',
      hint: 'Sum credits_spent from credit_transactions',
      icon: IconShield,
    },
  ];

  useEffect(() => {
    const days = timeRange === '7d' ? 7 : timeRange === '90d' ? 90 : 30;
    Promise.all([
      fetch(`/api/admin/analytics/revenue?days=${days}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null),
      fetch(`/api/admin/analytics/cohort?weeks=8`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null),
      fetch(`/api/admin/analytics/top-creators?metric=assistants&limit=10`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null),
    ]).then(([rev, coh, top]) => {
      setRevenueData(rev);
      setCohortData(coh);
      setTopCreators(top);
    });
  }, [timeRange]);

  return (
    <div className="p-8 space-y-8 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-[var(--fg-secondary)] max-w-xl">
          Tổng quan hệ thống. Số liệu thật từ Supabase (refresh mỗi lần vào page).
        </p>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="relative glass-strong rounded-2xl p-5 overflow-hidden animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div
                aria-hidden
                className="pointer-events-none absolute -top-12 -right-12 h-32 w-32 rounded-full bg-[var(--brand-500)] opacity-15 blur-2xl"
              />
              <div className="relative flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                    {card.label}
                  </p>
                  <p className="text-3xl font-bold tabular-nums">{card.value}</p>
                  <p className="text-xs text-[var(--fg-tertiary)] mt-2">
                    {card.hint}
                  </p>
                </div>
                <div className="shrink-0 h-10 w-10 rounded-xl bg-[var(--brand-500)]/20 flex items-center justify-center text-[var(--brand-300)]">
                  <Icon size={18} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Phase 11: Analytics Charts */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Analytics</h2>
          <div className="ml-auto flex gap-2">
            {(['7d', '30d', '90d'] as const).map(r => (
              <button key={r} onClick={() => setTimeRange(r)}
                className={`px-3 py-1 rounded text-xs ${
                  timeRange === r ? 'bg-[var(--brand-500)] text-white' : 'bg-[var(--surface)] border border-[var(--glass-border)]'
                }`}>
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Chart 1: Revenue */}
        {revenueData?.days?.length > 0 && (
          <div className="glass rounded-2xl p-5">
            <h3 className="text-lg font-semibold mb-3">Revenue ({revenueData.days_count} ngày)</h3>
            <Line
              data={{
                labels: revenueData.days,
                datasets: [
                  {
                    label: 'Credits Consumed',
                    data: revenueData.credits_consumed,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.3,
                    fill: true,
                  },
                  {
                    label: 'Active Users',
                    data: revenueData.users_active,
                    borderColor: 'rgb(236, 72, 153)',
                    backgroundColor: 'rgba(236, 72, 153, 0.1)',
                    tension: 0.3,
                    yAxisID: 'y1',
                  },
                ],
              }}
              options={{
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                scales: {
                  y: { type: 'linear', position: 'left', title: { display: true, text: 'Credits' } },
                  y1: { type: 'linear', position: 'right', title: { display: true, text: 'Users' }, grid: { drawOnChartArea: false } },
                },
              }}
            />
            <p className="text-xs text-[var(--fg-tertiary)] mt-2">Updated: {new Date(revenueData.cached_at).toLocaleString('vi-VN')}</p>
          </div>
        )}

        {/* Chart 2: Cohort Retention Table */}
        {cohortData?.cohorts?.length > 0 && (
          <div className="glass rounded-2xl p-5">
            <h3 className="text-lg font-semibold mb-3">
              Cohort Retention ({cohortData.cohorts.length} tuần)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--glass-border)]">
                    <th className="px-3 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Cohort</th>
                    <th className="px-3 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Size</th>
                    {Array.from({ length: 8 }, (_, i) => (
                      <th key={i} className="px-3 py-2 text-center text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">W{i}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cohortData.cohorts.map((c: any) => (
                    <tr key={c.week} className="border-b border-[var(--glass-border)]">
                      <td className="px-3 py-2 font-mono text-xs">{c.week}</td>
                      <td className="px-3 py-2 text-xs">{c.cohort_size}</td>
                      {c.retention.map((r: number, idx: number) => (
                        <td key={idx} className="px-3 py-2 text-center text-xs">
                          <span className="inline-block px-2 py-0.5 rounded" style={{
                            backgroundColor: `rgba(99, 102, 241, ${r})`,
                            color: r > 0.5 ? 'white' : 'var(--fg-secondary)',
                          }}>
                            {(r * 100).toFixed(0)}%
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Chart 3: Top Creators */}
        {topCreators?.creators?.length > 0 && (
          <div className="glass rounded-2xl p-5">
            <h3 className="text-lg font-semibold mb-3">Top Creators ({topCreators.creators.length})</h3>
            <div className="space-y-2">
              {topCreators.creators.map((c: any, idx: number) => (
                <div key={c.user_id} className="flex items-center gap-3 bg-[var(--surface)] rounded-lg p-3">
                  <span className="text-lg font-bold text-[var(--brand-300)] w-6">{idx + 1}</span>
                  <div className="flex-1">
                    <p className="text-sm font-semibold">{c.email}</p>
                    <p className="text-xs text-[var(--fg-tertiary)]">
                      {c.tier} · joined {new Date(c.created_at).toLocaleDateString('vi-VN')}
                    </p>
                  </div>
                  <span className="text-2xl font-bold text-[var(--brand-300)]">{c.metric_value}</span>
                  <span className="text-xs text-[var(--fg-tertiary)]">
                    {topCreators.metric === 'assistants' ? 'assistants' : 'credits'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-2">Phase 5 — Foundation</h2>
        <ul className="text-sm text-[var(--fg-secondary)] space-y-1 list-disc list-inside">
          <li>Migration 0022 đã được áp dụng (role, audit_logs, RPCs)</li>
          <li>Backend RBAC: <code className="text-[var(--brand-300)]">require_admin</code> dependency</li>
          <li>Audit log service với auto-mask sẵn sàng</li>
          <li>Phase 6 sẽ wire số liệu thật + thêm User/Credit management</li>
        </ul>
      </div>
    </div>
  );
}