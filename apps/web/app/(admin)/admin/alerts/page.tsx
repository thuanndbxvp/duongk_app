'use client';

import { useState } from 'react';
import { useArrayFetch } from '@/lib/use-fetch';

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  category: string;
  message: string;
  context: Record<string, any>;
  resolved_at: string | null;
  created_at: string;
}

export default function AdminAlertsPage() {
  const [showResolved, setShowResolved] = useState(false);
  const { data: alerts, loading, refresh } = useArrayFetch<Alert>(
    `/api/admin/alerts?include_resolved=${showResolved}`,
    [showResolved],
    'alerts'
  );

  async function handleResolve(id: string) {
    await fetch(`/api/admin/alerts/${id}/resolve`, { method: 'POST' });
    refresh();
  }

  const severityColor = (s: string) =>
    s === 'critical' ? 'bg-red-500/20 text-red-400' :
    s === 'warning' ? 'bg-orange-500/20 text-orange-400' :
    'bg-blue-500/20 text-blue-400';

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Alerts</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{alerts.filter(a => !a.resolved_at).length} unresolved</p>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={showResolved} onChange={(e) => setShowResolved(e.target.checked)}
          className="rounded" />
        <span>Show resolved</span>
      </label>

      {loading ? (
        <div className="text-center text-[var(--fg-tertiary)] py-12">Loading…</div>
      ) : alerts.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center text-[var(--fg-tertiary)]">
          No alerts 🎉
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.id} className={`glass rounded-2xl p-5 ${a.resolved_at ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${severityColor(a.severity)}`}>
                      {a.severity}
                    </span>
                    <span className="text-xs text-[var(--fg-tertiary)]">{a.category}</span>
                    <span className="text-xs text-[var(--fg-tertiary)]">
                      {new Date(a.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                  <p className="text-sm">{a.message}</p>
                  {Object.keys(a.context).length > 0 && (
                    <pre className="text-xs text-[var(--fg-tertiary)] bg-[var(--surface)] rounded p-2 overflow-x-auto">
                      {JSON.stringify(a.context, null, 2)}
                    </pre>
                  )}
                  {a.resolved_at && (
                    <p className="text-xs text-green-400">
                      ✓ Resolved {new Date(a.resolved_at).toLocaleString('vi-VN')}
                    </p>
                  )}
                </div>
                {!a.resolved_at && (
                  <button
                    onClick={() => handleResolve(a.id)}
                    className="px-3 py-1 rounded-lg bg-green-500/20 text-green-400 text-sm font-semibold shrink-0"
                  >
                    Resolve
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}