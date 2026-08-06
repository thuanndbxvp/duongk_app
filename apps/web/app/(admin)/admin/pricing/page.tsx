'use client';

import { useState } from 'react';
import { useArrayFetch } from '@/lib/use-fetch';

interface CreditPricing {
  id?: string;
  job_type: string;
  credits: number;
  enabled: boolean;
  description: string | null;
  updated_by: string | null;
  updated_at: string | null;
  created_at?: string;
}

export default function AdminPricingPage() {
  const { data: pricing, loading, refresh } = useArrayFetch<CreditPricing>('/api/admin/pricing', [], '_self');
  const [editing, setEditing] = useState<string | null>(null);
  const [formCredits, setFormCredits] = useState<number>(0);
  const [formDescription, setFormDescription] = useState<string>('');
  const [formEnabled, setFormEnabled] = useState<boolean>(true);
  const [saving, setSaving] = useState(false);
  const [reloading, setReloading] = useState(false);
  const [message, setMessage] = useState('');

  function startEdit(row: CreditPricing) {
    setEditing(row.job_type);
    setFormCredits(row.credits);
    setFormDescription(row.description || '');
    setFormEnabled(row.enabled);
    setMessage('');
  }

  function cancelEdit() {
    setEditing(null);
    setFormCredits(0);
    setFormDescription('');
    setFormEnabled(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setSaving(true);
    setMessage('');
    try {
      const res = await fetch(`/api/admin/pricing/${editing}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credits: formCredits,
          description: formDescription || null,
          enabled: formEnabled,
        }),
      });
      if (res.ok) {
        setMessage(`✓ Saved ${editing}`);
        setEditing(null);
        refresh();
      } else {
        const err = await res.json();
        setMessage(`✗ ${err.error || err.detail || 'unknown'}`);
      }
    } catch {
      setMessage('✗ Network error');
    } finally {
      setSaving(false);
    }
  }

  async function handleReload() {
    setReloading(true);
    setMessage('');
    try {
      const res = await fetch('/api/admin/pricing/reload', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setMessage(`✓ Cache reload queued (${data.note || ''})`);
      } else {
        setMessage(`✗ ${data.detail || 'Reload failed'}`);
      }
    } catch {
      setMessage('✗ Network error');
    } finally {
      setReloading(false);
    }
  }

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Pricing Config</h1>
          <p className="text-sm text-[var(--fg-tertiary)] mt-1">
            Quản lý credit per job type · {pricing.length} rows
          </p>
        </div>
        <button
          onClick={handleReload}
          disabled={reloading}
          className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50"
        >
          {reloading ? 'Reloading…' : 'Reload Cache'}
        </button>
      </div>

      {message && (
        <div
          className={`mb-4 p-3 rounded-lg text-sm ${
            message.startsWith('✓')
              ? 'bg-green-500/10 text-green-400 border border-green-500/20'
              : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}
        >
          {message}
        </div>
      )}

      {loading ? (
        <div className="glass rounded-2xl p-8 text-center text-[var(--fg-tertiary)]">
          Loading pricing…
        </div>
      ) : pricing.length === 0 ? (
        <div className="glass rounded-2xl p-8 text-center">
          <p className="text-[var(--fg-tertiary)]">
            No pricing rows. Add rows via Supabase Dashboard → credit_pricing table.
          </p>
        </div>
      ) : (
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--glass-border)] bg-[var(--surface)]">
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Job Type
                </th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Credits
                </th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Enabled
                </th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Description
                </th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Updated
                </th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-wider font-semibold text-[var(--fg-tertiary)]">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {pricing.map((row) => (
                <tr
                  key={row.job_type}
                  className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)]"
                >
                  {editing === row.job_type ? (
                    <>
                      <td className="px-4 py-3 font-mono text-xs">{row.job_type}</td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          min="0"
                          value={formCredits}
                          onChange={(e) => setFormCredits(Number(e.target.value))}
                          className="w-20 px-2 py-1 rounded border border-[var(--glass-border)] bg-[var(--surface)]"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={formEnabled}
                          onChange={(e) => setFormEnabled(e.target.checked)}
                          className="w-4 h-4"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={formDescription}
                          onChange={(e) => setFormDescription(e.target.value)}
                          placeholder="Optional description"
                          className="w-full px-2 py-1 rounded border border-[var(--glass-border)] bg-[var(--surface)]"
                        />
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">—</td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <button
                          onClick={handleSave}
                          disabled={saving}
                          className="px-3 py-1 rounded bg-[var(--brand-500)] text-white text-xs hover:opacity-90 disabled:opacity-50"
                        >
                          {saving ? 'Saving…' : 'Save'}
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="px-3 py-1 rounded border border-[var(--glass-border)] text-xs hover:bg-[var(--surface-hover)]"
                        >
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-[var(--brand-300)]">
                        {row.job_type}
                      </td>
                      <td className="px-4 py-3 font-bold">{row.credits}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold ${
                            row.enabled
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}
                        >
                          {row.enabled ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--fg-secondary)] max-w-xs truncate">
                        {row.description || '—'}
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                        {row.updated_at
                          ? new Date(row.updated_at).toLocaleDateString('vi-VN')
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => startEdit(row)}
                          className="px-3 py-1 rounded border border-[var(--glass-border)] text-xs hover:bg-[var(--surface-hover)]"
                        >
                          Edit
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6 glass rounded-2xl p-4 text-xs text-[var(--fg-tertiary)]">
        <p className="font-semibold mb-1">Notes:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Thay đổi pricing sẽ ghi audit log vào admin_audit_logs (action: pricing.update).</li>
          <li>Sau khi update, bấm "Reload Cache" để worker reload pricing từ DB.</li>
          <li>Phase 6 stub: /reload endpoint chỉ log, Redis pub/sub thật ở Phase 7+.</li>
        </ul>
      </div>
    </div>
  );
}
