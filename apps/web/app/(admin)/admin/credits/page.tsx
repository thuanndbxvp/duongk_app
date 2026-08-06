'use client';

import { useMemo, useState } from 'react';
import { buildQuery, useArrayFetch, useObjectFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';

interface Transaction {
  id: string;
  user_id: string;
  action: string;
  amount: number;
  balance_after: number;
  reason: string;
  created_at: string;
  users?: { email: string };
}

interface Stats {
  total_issued: number;
  total_spent: number;
  total_hold: number;
  total_refunded: number;
  sparkline: Array<{ date: string; spent: number }>;
}

// Map action key → nhãn tiếng Việt + màu sắc.
const ACTION_META: Record<string, { label: string; color: string }> = {
  issue: { label: 'Cấp', color: 'bg-green-500/20 text-green-400' },
  spend: { label: 'Tiêu', color: 'bg-red-500/20 text-red-400' },
  refund: { label: 'Hoàn', color: 'bg-blue-500/20 text-blue-400' },
  hold: { label: 'Giữ', color: 'bg-yellow-500/20 text-yellow-400' },
  release: { label: 'Giải phóng', color: 'bg-purple-500/20 text-purple-400' },
  adjust: { label: 'Điều chỉnh', color: 'bg-[var(--brand-500)]/20 text-[var(--brand-300)]' },
};

const DEFAULT_ACTION_OPTIONS = [
  { value: '', label: 'Tất cả hành động' },
  { value: 'issue', label: 'Cấp credit' },
  { value: 'spend', label: 'Tiêu credit' },
  { value: 'refund', label: 'Hoàn credit' },
  { value: 'hold', label: 'Giữ credit' },
  { value: 'release', label: 'Giải phóng credit' },
  { value: 'adjust', label: 'Điều chỉnh' },
];

export default function AdminCreditsPage() {
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [actionFilter, setActionFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const url = useMemo(
    () =>
      `/api/admin/credit/ledger${buildQuery({
        page,
        limit,
        action: actionFilter,
        user_id: emailFilter.trim(),
        from_date: fromDate ? `${fromDate}T00:00:00` : null,
        to_date: toDate ? `${toDate}T23:59:59` : null,
      })}`,
    [page, limit, actionFilter, emailFilter, fromDate, toDate],
  );

  const { data: txs, total, loading, error } = useArrayFetch<Transaction>(
    url,
    [page, limit, actionFilter, emailFilter, fromDate, toDate],
    'transactions',
  );

  const { data: stats } = useObjectFetch<Stats>('/api/admin/credit/stats', []);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const sparklineMax = useMemo(
    () => Math.max(1, ...(stats?.sparkline?.map((s) => s.spent) ?? [1])),
    [stats],
  );

  const totalSpentLast7Days = useMemo(
    () => stats?.sparkline?.reduce((acc, d) => acc + d.spent, 0) ?? 0,
    [stats],
  );

  function handleExport() {
    const from = fromDate || new Date(Date.now() - 30 * 86400_000).toISOString().slice(0, 10);
    const to = toDate || new Date().toISOString().slice(0, 10);
    window.location.href = `/api/admin/credit/export?from_date=${from}&to_date=${to}`;
  }

  function clearFilters() {
    setActionFilter('');
    setEmailFilter('');
    setFromDate('');
    setToDate('');
    setPage(1);
  }

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Quản trị
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Sổ cái Credit</span>
        </h1>
        <p className="text-sm text-[var(--fg-tertiary)]">
          Theo dõi toàn bộ biến động credit trong hệ thống — lọc, phân trang, xuất CSV.
        </p>
      </div>

      {/* Thẻ thống kê */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: 'Tổng đã cấp', value: stats?.total_issued ?? 0, color: 'text-green-400', tooltip: 'Tổng credit đã cấp cho người dùng (trừ hoàn)' },
          { label: 'Tổng đã tiêu', value: stats?.total_spent ?? 0, color: 'text-red-400', tooltip: 'Tổng credit người dùng đã sử dụng' },
          { label: 'Đang giữ', value: stats?.total_hold ?? 0, color: 'text-yellow-400', tooltip: 'Credit đang được giữ bởi các job đang chạy' },
          { label: 'Tổng hoàn', value: stats?.total_refunded ?? 0, color: 'text-blue-400', tooltip: 'Tổng credit đã hoàn lại cho người dùng' },
        ].map((s) => (
          <div key={s.label} className="glass-strong rounded-2xl p-5" title={s.tooltip}>
            <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">{s.label}</p>
            <p className={`text-3xl font-bold tabular-nums ${s.color}`}>{s.value.toLocaleString('vi-VN')}</p>
          </div>
        ))}
      </div>

      {/* Biểu đồ 7 ngày */}
      {stats?.sparkline && stats.sparkline.length > 0 && (
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">
                Lượt tiêu — 7 ngày gần nhất
              </p>
              <p className="text-2xl font-bold tabular-nums text-red-400 mt-1">
                {totalSpentLast7Days.toLocaleString('vi-VN')}
              </p>
            </div>
            <span className="text-xs text-[var(--fg-tertiary)]">
              Tổng 7 ngày
            </span>
          </div>
          <div className="flex items-end gap-2 h-24">
            {stats.sparkline.map((d) => {
              const heightPct = Math.max(4, (d.spent / sparklineMax) * 100);
              const day = new Date(d.date);
              const dayLabel = day.toLocaleDateString('vi-VN', {
                weekday: 'short',
                day: '2-digit',
              });
              const fullDate = day.toLocaleDateString('vi-VN');
              return (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1 min-w-0">
                  <div className="text-[10px] text-[var(--fg-tertiary)] tabular-nums">
                    {d.spent > 0 ? d.spent.toLocaleString('vi-VN') : '—'}
                  </div>
                  <div
                    className="w-full rounded-t bg-gradient-to-t from-red-500/30 to-red-400/70 transition-all cursor-help"
                    style={{ height: `${heightPct}%` }}
                    title={`${fullDate}: ${d.spent.toLocaleString('vi-VN')} credit đã tiêu`}
                  />
                  <div className="text-[10px] text-[var(--fg-tertiary)] truncate w-full text-center">
                    {dayLabel}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Bộ lọc + xuất */}
      <div className="glass rounded-2xl p-4">
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-2">
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Mã người dùng (UUID)
            </label>
            <input
              type="text"
              value={emailFilter}
              onChange={(e) => { setEmailFilter(e.target.value); setPage(1); }}
              placeholder="Dán UUID người dùng"
              className="w-full h-9 px-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Hành động
            </label>
            <Select
              value={actionFilter}
              onChange={(v) => { setActionFilter(v); setPage(1); }}
              options={DEFAULT_ACTION_OPTIONS}
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Từ ngày
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => { setFromDate(e.target.value); setPage(1); }}
              className="w-full h-9 px-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Đến ngày
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => { setToDate(e.target.value); setPage(1); }}
              className="w-full h-9 px-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors"
            />
          </div>
        </div>
        <div className="flex items-center justify-between mt-3 gap-2">
          <button
            onClick={clearFilters}
            className="text-xs text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] transition-colors"
          >
            Xoá bộ lọc
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white text-sm font-semibold hover:bg-[var(--brand-400)] transition-colors"
          >
            Xuất CSV
          </button>
        </div>
      </div>

      {/* Lỗi */}
      {error && (
        <div className="rounded-xl px-4 py-3 text-sm border border-red-500/40 bg-red-500/10 text-red-300">
          {error}
        </div>
      )}

      {/* Bảng giao dịch */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--bg-surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Người dùng
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Hành động
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Số lượng
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Số dư sau
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Lý do
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
                Thời gian
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">
                  Đang tải giao dịch…
                </td>
              </tr>
            ) : txs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">
                  Không có giao dịch nào khớp với bộ lọc.
                </td>
              </tr>
            ) : (
              txs.map((tx) => {
                const actionMeta = ACTION_META[tx.action];
                const actionClass = actionMeta?.color || 'bg-[var(--brand-500)]/20 text-[var(--brand-300)]';
                const actionLabel = actionMeta?.label || tx.action;
                return (
                  <tr key={tx.id} className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)] transition-colors">
                    <td className="px-4 py-3 text-[var(--fg-secondary)]">
                      {tx.users?.email || (
                        <span className="font-mono text-xs">{tx.user_id.slice(0, 8)}…</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${actionClass}`}>
                        {actionLabel}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-right tabular-nums font-semibold ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {tx.amount > 0 ? '+' : ''}
                      {tx.amount.toLocaleString('vi-VN')}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-[var(--fg-secondary)]">
                      {tx.balance_after.toLocaleString('vi-VN')}
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)] max-w-xs truncate" title={tx.reason || ''}>
                      {tx.reason || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)] whitespace-nowrap">
                      {new Date(tx.created_at).toLocaleString('vi-VN')}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Phân trang */}
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs text-[var(--fg-tertiary)]">
          Hiển thị {txs.length} / {total.toLocaleString('vi-VN')} giao dịch
        </p>
        <div className="flex items-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="h-9 px-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] disabled:opacity-30 transition-colors hover:border-[var(--brand-400)]/50"
          >
            ← Trước
          </button>
          <span className="text-xs text-[var(--fg-tertiary)] tabular-nums">
            Trang {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="h-9 px-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] disabled:opacity-30 transition-colors hover:border-[var(--brand-400)]/50"
          >
            Sau →
          </button>
        </div>
      </div>
    </div>
  );
}
