'use client';

import { useState } from 'react';
import { useArrayFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';

const PROVIDER_OPTIONS = [
  'openai', 'cohere', 'modal', 'r2', 'supadata', 'serpapi',
  'youtube', 'elevenlabs', 'pexels', 'pixabay', 'unsplash',
  'supabase_service_role', 'groq',
].map((p) => ({ value: p, label: p }));

interface ApiKey {
  id: string;
  provider: string;
  label: string;
  is_active: boolean;
  rate_limit_rpm: number | null;
  monthly_budget_usd: number | null;
  current_month_cost_usd: number;
  last_tested_at: string | null;
  last_test_status: string | null;
  last_test_latency_ms: number | null;
  expires_at: string | null;
  archived_at: string | null;
  created_at: string;
}

export default function AdminApiKeysPage() {
  const { data: keys, loading, refresh } = useArrayFetch<ApiKey>('/api/admin/api-keys', [], 'keys');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [formProvider, setFormProvider] = useState('openai');
  const [formLabel, setFormLabel] = useState('');
  const [formValue, setFormValue] = useState('');
  const [formBudget, setFormBudget] = useState('');
  const [message, setMessage] = useState('');

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setMessage('');
    const res = await fetch('/api/admin/api-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: formProvider,
        label: formLabel,
        value: formValue,
        monthly_budget_usd: formBudget ? Number(formBudget) : null,
      }),
    });
    if (res.ok) {
      setMessage('✓ Created');
      setShowCreate(false);
      setFormLabel(''); setFormValue(''); setFormBudget('');
      refresh();
    } else {
      const err = await res.json();
      setMessage(`Error: ${err.detail || 'unknown'}`);
    }
    setCreating(false);
  }

  async function handleTest(id: string) {
    setMessage('');
    const res = await fetch(`/api/admin/api-keys/${id}/test`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      setMessage(`✓ Test OK (${data.latency_ms}ms)`);
    } else {
      setMessage(`✗ Test failed: ${data.error}`);
    }
    refresh();
  }

  async function handleRotate(id: string, label: string) {
    const newValue = prompt(`New value for ${label}:`);
    if (!newValue) return;
    const res = await fetch(`/api/admin/api-keys/${id}/rotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_value: newValue }),
    });
    if (res.ok) {
      setMessage('✓ Rotated');
      refresh();
    } else {
      setMessage('✗ Rotate failed');
    }
  }

  // Group by provider
  const byProvider = keys.reduce((acc, k) => {
    acc[k.provider] = acc[k.provider] || [];
    acc[k.provider].push(k);
    return acc;
  }, {} as Record<string, ApiKey[]>);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">API Keys</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{keys.length} keys total</p>
      </div>

      {message && <div className="glass rounded-xl p-3 text-sm">{message}</div>}

      <button
        onClick={() => setShowCreate(!showCreate)}
        className="h-9 px-4 rounded-lg bg-[var(--brand-500)] text-sm font-semibold text-white hover:bg-[var(--brand-400)] transition-colors"
      >
        {showCreate ? 'Cancel' : '+ Add Key'}
      </button>

      {showCreate && (
        <form onSubmit={handleCreate} className="glass rounded-2xl p-5 space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <Select
              value={formProvider}
              onChange={setFormProvider}
              options={PROVIDER_OPTIONS}
            />
            <input type="text" value={formLabel} onChange={(e) => setFormLabel(e.target.value)} required
              placeholder="Label (e.g. 'OpenAI key #1')"
              className="h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors" />
          </div>
          <input type="password" value={formValue} onChange={(e) => setFormValue(e.target.value)} required
            placeholder="API key value (sẽ được encrypt)"
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors" />
          <input type="number" step="0.01" value={formBudget} onChange={(e) => setFormBudget(e.target.value)}
            placeholder="Monthly budget USD (optional)"
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors" />
          <button type="submit" disabled={creating}
            className="w-full h-9 rounded-lg bg-[var(--brand-500)] text-sm font-semibold text-white hover:bg-[var(--brand-400)] disabled:opacity-50 transition-colors">
            {creating ? 'Encrypting…' : 'Create + Encrypt'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="text-center text-[var(--fg-tertiary)] py-12">Loading…</div>
      ) : Object.keys(byProvider).length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center text-[var(--fg-tertiary)]">No keys</div>
      ) : (
        Object.entries(byProvider).map(([provider, pkeys]) => (
          <div key={provider} className="glass rounded-2xl overflow-hidden">
            <div className="px-5 py-3 bg-[var(--surface)] border-b border-[var(--glass-border)]">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--fg-tertiary)]">
                {provider} · {pkeys.length} key{pkeys.length !== 1 ? 's' : ''}
              </h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
                <tr>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Label</th>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Status</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Budget</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Cost (mo)</th>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Last test</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pkeys.map((k) => (
                  <tr key={k.id} className="border-b border-[var(--glass-border)]">
                    <td className="px-4 py-3 text-white">{k.label}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                        !k.is_active ? 'bg-gray-500/20 text-gray-400' :
                        k.archived_at ? 'bg-red-500/20 text-red-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {k.archived_at ? 'archived' : k.is_active ? 'active' : 'inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {k.monthly_budget_usd ? `$${k.monthly_budget_usd}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      ${(k.current_month_cost_usd || 0).toFixed(4)}
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                      {k.last_test_status ? (
                        <span className={k.last_test_status === 'ok' ? 'text-green-400' : 'text-red-400'}>
                          {k.last_test_status} · {k.last_test_latency_ms}ms
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={() => handleTest(k.id)}
                        className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">
                        Test
                      </button>
                      <button onClick={() => handleRotate(k.id, k.label)}
                        className="text-xs px-2 py-1 rounded bg-orange-500/20 text-orange-400">
                        Rotate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}