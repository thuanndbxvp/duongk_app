'use client';

interface TrafficData {
  requests_per_day?: { date: string; count: number }[];
  top_endpoints?: { path: string; count: number; p95_ms: number }[];
  error_rate?: number;
  active_users?: number;
}

export function TrafficChart({ data }: { data: TrafficData | null }) {
  if (!data) return <p className="text-[var(--fg-tertiary)]">No traffic data available.</p>;

  const maxCount = Math.max(...(data.requests_per_day || [{ count: 1 }]).map(d => d.count), 1);

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-strong rounded-xl p-4 text-center">
          <p className="text-2xl font-bold">{data.active_users || 0}</p>
          <p className="text-xs text-[var(--fg-tertiary)]">Active Users</p>
        </div>
        <div className="glass-strong rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-red-400">{(data.error_rate || 0) * 100}%</p>
          <p className="text-xs text-[var(--fg-tertiary)]">Error Rate</p>
        </div>
        <div className="glass-strong rounded-xl p-4 text-center">
          <p className="text-2xl font-bold">{data.top_endpoints?.length || 0}</p>
          <p className="text-xs text-[var(--fg-tertiary)]">Endpoints</p>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="glass-strong rounded-xl p-4 space-y-2">
        <h3 className="text-sm font-semibold">Requests per Day</h3>
        <div className="flex items-end gap-1 h-32">
          {(data.requests_per_day || []).map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
              <div className="w-full gradient-bg rounded-t" style={{ height: `${(d.count / maxCount) * 100}%`, minHeight: 4 }} />
              <span className="text-[8px] text-[var(--fg-tertiary)] mt-1">{d.date?.slice(5)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Endpoints */}
      <div className="glass-strong rounded-xl p-4 space-y-2">
        <h3 className="text-sm font-semibold">Top Endpoints</h3>
        {(data.top_endpoints || []).slice(0, 10).map((e, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="text-[var(--fg-secondary)] truncate flex-1 mr-3">{e.path}</span>
            <span className="text-[var(--fg-tertiary)] w-16 text-right">{e.count} req</span>
            <span className="text-[var(--fg-tertiary)] w-16 text-right">{e.p95_ms}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}
