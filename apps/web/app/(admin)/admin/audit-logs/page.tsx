'use client';

import { useState } from 'react';
import { buildQuery, useArrayFetch } from '@/lib/use-fetch';

interface AuditLog {
  id: string;
  admin_email: string;
  action: string;
  target_type: string;
  target_id: string | null;
  before: Record<string, any> | null;
  after: Record<string, any> | null;
  ip: string | null;
  user_agent: string | null;
  reason: string | null;
  created_at: string;
}

export default function AdminAuditLogsPage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [targetFilter, setTargetFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const url = `/api/admin/audit-logs${buildQuery({
    page,
    limit: 50,
    action: actionFilter,
    target_type: targetFilter,
    admin_email: emailFilter,
  })}`;
  const { data: logs, total, loading } = useArrayFetch<AuditLog>(url, [page, actionFilter, targetFilter, emailFilter], 'logs');

  async function openDetail(id: string) {
    const res = await fetch(`/api/admin/audit-logs/${id}`);
    if (res.ok) setSelectedLog(await res.json());
  }

  function handleExport() {
    const from = prompt('From date (YYYY-MM-DD):');
    if (!from) return;
    const to = prompt('To date (YYYY-MM-DD, max 30 days from from):');
    if (!to) return;
    window.location.href = `/api/admin/audit-logs/export/csv?from_date=${from}T00:00:00Z&to_date=${to}T23:59:59Z`;
  }

  const totalPages = Math.ceil(total / 50);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Audit Logs</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{total} entries</p>
      </div>

      {/* Filters */}
      <div className="glass rounded-2xl p-4 flex flex-wrap gap-3">
        <input
          type="text" placeholder="Admin email…"
          value={emailFilter} onChange={(e) => { setEmailFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <input
          type="text" placeholder="Action (vd: user.update)…"
          value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <input
          type="text" placeholder="Target type (vd: user)…"
          value={targetFilter} onChange={(e) => { setTargetFilter(e.target.value); setPage(1); }}
          className="flex-1 min-w-[150px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
        />
        <button
          onClick={handleExport}
          className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Admin</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Action</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Target</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Reason</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">Loading…</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">No logs</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id} onClick={() => openDetail(log.id)}
                className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)] cursor-pointer">
                <td className="px-4 py-3 text-[var(--brand-300)]">{log.admin_email}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {log.target_type}/{log.target_id?.slice(0, 12)}…
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)] max-w-xs truncate">
                  {log.reason || '—'}
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {new Date(log.created_at).toLocaleString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button disabled={page === 1} onClick={() => setPage(page - 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30">
            ← Previous
          </button>
          <span className="text-sm text-[var(--fg-tertiary)]">Page {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(page + 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30">
            Next →
          </button>
        </div>
      )}

      {/* JSON Diff Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
          onClick={() => setSelectedLog(null)}>
          <div className="glass-strong rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedLog.action}</h2>
                <p className="text-sm text-[var(--fg-tertiary)]">
                  {selectedLog.admin_email} · {new Date(selectedLog.created_at).toLocaleString('vi-VN')}
                </p>
              </div>
              <button onClick={() => setSelectedLog(null)}
                className="text-2xl text-[var(--fg-tertiary)] hover:text-white">×</button>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold mb-2 text-red-400">Before</h3>
                <pre className="text-xs bg-[var(--surface)] rounded p-3 overflow-x-auto max-h-96">
                  {JSON.stringify(selectedLog.before, null, 2) || 'null'}
                </pre>
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-2 text-green-400">After</h3>
                <pre className="text-xs bg-[var(--surface)] rounded p-3 overflow-x-auto max-h-96">
                  {JSON.stringify(selectedLog.after, null, 2) || 'null'}
                </pre>
              </div>
            </div>
            {selectedLog.reason && (
              <div className="mt-4 text-sm">
                <strong>Reason:</strong> {selectedLog.reason}
              </div>
            )}
            <div className="mt-4 text-xs text-[var(--fg-tertiary)]">
              IP: {selectedLog.ip || '—'} · UA: {selectedLog.user_agent?.slice(0, 50) || '—'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}