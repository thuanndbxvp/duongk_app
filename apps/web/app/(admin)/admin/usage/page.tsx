'use client';

import { useEffect, useState } from 'react';
import { useArrayFetch, useObjectFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';

// =============================================================================
// Types
// =============================================================================

interface ApiUsageLog {
  id: string;
  user_id: string;
  feature: string;
  provider: string;
  api_key_id: string | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: string;
  error_message: string | null;
  created_at: string;
  // Expanded fields
  user_email?: string;
  api_key_alias?: string;
}

interface UsageStats {
  total_calls: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  avg_latency_ms: number;
  success_rate: number;
  by_feature: Record<string, { calls: number; cost: number }>;
  by_provider: Record<string, { calls: number; cost: number }>;
}

interface UsageFilter {
  feature?: string;
  provider?: string;
  status?: string;
  user_id?: string;
  date_from?: string;
  date_to?: string;
}

// =============================================================================
// Constants
// =============================================================================

const FEATURE_OPTIONS = [
  { value: '', label: 'All Features' },
  { value: 'transcript_extract', label: 'Transcript Extract' },
  { value: 'llm_text', label: 'LLM Text' },
  { value: 'embedding', label: 'Embedding' },
  { value: 'emotion_classifier', label: 'Emotion Classifier' },
  { value: 'ffmpeg_render', label: 'FFmpeg Render' },
  { value: 'tts', label: 'Text-to-Speech' },
  { value: 'thumbnail_vision', label: 'Thumbnail Vision' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'success', label: 'Success' },
  { value: 'error', label: 'Error' },
  { value: 'timeout', label: 'Timeout' },
];

// =============================================================================
// Main Page
// =============================================================================

export default function AdminUsagePage() {
  const [logs, setLogs] = useState<ApiUsageLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [filter, setFilter] = useState<UsageFilter>({});
  const pageSize = 50;

  // Fetch stats
  useEffect(() => {
    fetch('/api/admin/analytics/usage-stats')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setStats(data))
      .catch(() => null);
  }, []);

  // Fetch logs
  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
      page: String(page),
      limit: String(pageSize),
    });
    if (filter.feature) params.set('feature', filter.feature);
    if (filter.provider) params.set('provider', filter.provider);
    if (filter.status) params.set('status', filter.status);
    if (filter.date_from) params.set('date_from', filter.date_from);
    if (filter.date_to) params.set('date_to', filter.date_to);

    fetch(`/api/admin/usage-logs?${params}`)
      .then(r => r.ok ? r.json() : { data: [], total: 0, page: 1, total_pages: 1 })
      .then(data => {
        setLogs(data.data || []);
        setPage(data.page || 1);
        setTotalPages(data.total_pages || 1);
      })
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, [page, filter]);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">API Usage</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Real-time API usage logs từ bảng <code className="text-[var(--brand-300)]">api_usage_logs</code>.
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-4">
          <StatCard
            label="Total Calls"
            value={stats.total_calls.toLocaleString()}
            sub={`${(stats.success_rate * 100).toFixed(1)}% success`}
          />
          <StatCard
            label="Total Cost"
            value={`$${stats.total_cost_usd.toFixed(2)}`}
            sub={`Avg $${(stats.total_cost_usd / (stats.total_calls || 1)).toFixed(4)}/call`}
          />
          <StatCard
            label="Input Tokens"
            value={(stats.total_input_tokens / 1000).toFixed(1) + 'K'}
            sub=""
          />
          <StatCard
            label="Output Tokens"
            value={(stats.total_output_tokens / 1000).toFixed(1) + 'K'}
            sub=""
          />
          <StatCard
            label="Avg Latency"
            value={`${stats.avg_latency_ms.toFixed(0)}ms`}
            sub=""
          />
        </div>
      )}

      {/* Filters */}
      <div className="glass rounded-2xl p-4">
        <div className="flex flex-wrap gap-4">
          <div className="space-y-1">
            <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Feature</label>
            <Select
              value={filter.feature || ''}
              onChange={(v) => setFilter({ ...filter, feature: v || undefined })}
              options={FEATURE_OPTIONS}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Status</label>
            <Select
              value={filter.status || ''}
              onChange={(v) => setFilter({ ...filter, status: v || undefined })}
              options={STATUS_OPTIONS}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">From</label>
            <input
              type="date"
              value={filter.date_from || ''}
              onChange={(e) => setFilter({ ...filter, date_from: e.target.value || undefined })}
              className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">To</label>
            <input
              type="date"
              value={filter.date_to || ''}
              onChange={(e) => setFilter({ ...filter, date_to: e.target.value || undefined })}
              className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm"
            />
          </div>
          <div className="ml-auto flex items-end">
            <button
              onClick={() => setFilter({})}
              className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm hover:bg-[var(--brand-500)]/10"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Usage Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--glass-border)] bg-[var(--surface)]/50">
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Time</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">User</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Feature</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Provider</th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Tokens In</th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Tokens Out</th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Cost</th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Latency</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-[var(--fg-tertiary)]">
                    Loading…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-[var(--fg-tertiary)]">
                    No logs found
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-[var(--glass-border)] hover:bg-[var(--surface)]/30">
                    <td className="px-4 py-3 text-xs font-mono text-[var(--fg-tertiary)]">
                      {new Date(log.created_at).toLocaleString('vi-VN')}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {log.user_email || log.user_id.slice(0, 8)}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <span className="px-2 py-0.5 rounded bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                        {log.feature}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--fg-secondary)]">
                      {log.provider}
                    </td>
                    <td className="px-4 py-3 text-xs text-right tabular-nums">
                      {log.input_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-xs text-right tabular-nums">
                      {log.output_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-xs text-right tabular-nums text-[var(--brand-300)]">
                      ${log.cost_usd.toFixed(6)}
                    </td>
                    <td className="px-4 py-3 text-xs text-right tabular-nums">
                      {log.latency_ms}ms
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        log.status === 'success' ? 'bg-green-500/20 text-green-400' :
                        log.status === 'error' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--glass-border)]">
          <span className="text-xs text-[var(--fg-tertiary)]">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 rounded bg-[var(--surface)] border border-[var(--glass-border)] text-xs disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1 rounded bg-[var(--surface)] border border-[var(--glass-border)] text-xs disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Stat Card Component
// =============================================================================

function StatCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="glass rounded-xl p-4">
      <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs text-[var(--fg-tertiary)] mt-1">{sub}</p>}
    </div>
  );
}
