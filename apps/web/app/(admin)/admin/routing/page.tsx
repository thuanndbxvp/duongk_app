'use client';

import { useEffect, useState } from 'react';
import { useArrayFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';

interface RoutingConfig {
  id: string;
  feature: string;
  primary_provider: string;
  fallback_chain: string[];
  enabled_providers: Record<string, boolean>;
  cost_per_call_usd: Record<string, number>;
  config_version: number;
  cost_estimate_7d?: Record<string, { avg_cost_usd: number; total_calls: number; success_rate: number }>;
}

const FEATURE_LABELS: Record<string, string> = {
  transcript_extract: 'Transcript Extract',
  llm_text: 'LLM Text (Script Gen)',
  embedding: 'Embedding (RAG)',
  emotion_classifier: 'Emotion Classifier',
  ffmpeg_render: 'FFmpeg Render',
  tts: 'Text-to-Speech',
  thumbnail_vision: 'Thumbnail Vision',
  footage_search: 'Footage Search',
};

export default function AdminRoutingPage() {
  const { data: fetched, loading: loadingList, refresh } = useArrayFetch<RoutingConfig>(
    '/api/admin/routing-config',
    [],
    'configs'
  );
  const [configs, setConfigs] = useState<RoutingConfig[]>([]);
  useEffect(() => {
    setConfigs(fetched);
  }, [fetched]);
  const loading = loadingList && configs.length === 0;
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  async function handleSave(config: RoutingConfig) {
    setSaving(config.feature);
    setMessage('');
    const res = await fetch(`/api/admin/routing-config/${config.feature}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_provider: config.primary_provider,
        fallback_chain: config.fallback_chain,
        enabled_providers: config.enabled_providers,
        cost_per_call_usd: config.cost_per_call_usd,
        expected_version: config.config_version,
      }),
    });
    if (res.ok) {
      setMessage(`✓ ${config.feature} updated (worker sẽ reload trong < 60s)`);
      refresh();
    } else if (res.status === 409) {
      setMessage(`✗ Conflict — config đã bị sửa bởi admin khác. Reload.`);
      refresh();
    } else {
      const err = await res.json();
      setMessage(`✗ Error: ${err.detail}`);
    }
    setSaving(null);
  }

  async function handleReload(feature: string) {
    await fetch(`/api/admin/routing-config/${feature}/reload`, { method: 'POST' });
    setMessage(`✓ ${feature} reload queued`);
  }

  if (loading) return <div className="p-8 text-center text-[var(--fg-tertiary)]">Loading…</div>;

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Service Routing</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{configs.length} features · Hot-reload qua Redis pub/sub</p>
      </div>

      {message && <div className="glass rounded-xl p-3 text-sm">{message}</div>}

      <div className="grid lg:grid-cols-2 gap-4">
        {configs.map((config) => (
          <RoutingCard
            key={config.feature}
            config={config}
            saving={saving === config.feature}
            onSave={handleSave}
            onReload={handleReload}
            onChange={setConfigs}
          />
        ))}
      </div>
    </div>
  );
}

function RoutingCard({
  config, saving, onSave, onReload, onChange,
}: {
  config: RoutingConfig;
  saving: boolean;
  onSave: (c: RoutingConfig) => void;
  onReload: (f: string) => void;
  onChange: (configs: RoutingConfig[]) => void;
}) {
  const allProviders = Array.from(new Set([
    config.primary_provider,
    ...config.fallback_chain,
    ...Object.keys(config.enabled_providers),
  ]));
  
  function updateConfig(patch: Partial<RoutingConfig>) {
    onChange([{ ...config, ...patch }]);
  }

  function moveProvider(idx: number, delta: number) {
    const chain = [...config.fallback_chain];
    const target = idx + delta;
    if (target < 0 || target >= chain.length) return;
    [chain[idx], chain[target]] = [chain[target], chain[idx]];
    updateConfig({ fallback_chain: chain });
  }

  return (
    <div className="glass rounded-2xl p-5 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold">{FEATURE_LABELS[config.feature] || config.feature}</h3>
          <p className="text-xs text-[var(--fg-tertiary)]">{config.feature} · v{config.config_version}</p>
        </div>
        <button
          onClick={() => onReload(config.feature)}
          className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400"
        >
          Reload
        </button>
      </div>

      {/* Primary provider */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Primary</label>
        <div className="mt-1">
          <Select
            value={config.primary_provider}
            onChange={(v) => updateConfig({ primary_provider: v })}
            options={allProviders.map((p) => ({ value: p, label: p }))}
          />
        </div>
      </div>

      {/* Fallback chain */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Fallback chain</label>
        <div className="mt-1 space-y-1">
          {config.fallback_chain.map((provider, idx) => (
            <div key={provider} className="flex items-center gap-2 bg-[var(--surface)] rounded-lg px-2 py-1">
              <span className="text-xs text-[var(--fg-tertiary)] w-6">{idx + 1}.</span>
              <span className="flex-1 text-sm">{provider}</span>
              <button onClick={() => moveProvider(idx, -1)} disabled={idx === 0} className="text-xs px-1 text-[var(--fg-tertiary)]">↑</button>
              <button onClick={() => moveProvider(idx, 1)} disabled={idx === config.fallback_chain.length - 1} className="text-xs px-1 text-[var(--fg-tertiary)]">↓</button>
            </div>
          ))}
        </div>
      </div>

      {/* Enabled providers */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Enabled</label>
        <div className="mt-1 space-y-1">
          {allProviders.map(provider => (
            <label key={provider} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={config.enabled_providers[provider] ?? false}
                onChange={(e) => updateConfig({
                  enabled_providers: { ...config.enabled_providers, [provider]: e.target.checked },
                })}
              />
              <span className="flex-1">{provider}</span>
              <span className="text-xs text-[var(--fg-tertiary)]">
                ${config.cost_per_call_usd[provider]?.toFixed(4) || '0.0000'}/call
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Cost preview (7d) */}
      {config.cost_estimate_7d && Object.keys(config.cost_estimate_7d).length > 0 && (
        <div className="text-xs text-[var(--fg-tertiary)] space-y-1 bg-[var(--surface)] rounded-lg p-2">
          <p className="font-semibold">7d cost estimate:</p>
          {Object.entries(config.cost_estimate_7d).map(([keyId, stats]) => (
            <p key={keyId}>{keyId.slice(0, 8)}…: ${stats.avg_cost_usd.toFixed(4)} avg · {stats.total_calls} calls · {(stats.success_rate * 100).toFixed(1)}% success</p>
          ))}
        </div>
      )}

      <button
        onClick={() => onSave(config)}
        disabled={saving}
        className="w-full px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save + Hot Reload'}
      </button>
    </div>
  );
}