'use client';

export function ScrapeJobList({ jobs }: { jobs: { id: string; channel_id: string; status: string; created_at: string }[] }) {
  if (!jobs || jobs.length === 0) return <p className="text-xs text-[var(--fg-tertiary)]">No recent jobs.</p>;
  return (
    <div className="space-y-2">
      {jobs.slice(0, 10).map(j => (
        <div key={j.id} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04]">
          <span className="text-xs text-[var(--fg-secondary)]">{j.id.slice(0, 8)}...</span>
          <span className={`text-[10px] px-2 py-0.5 rounded ${
            j.status === 'completed' ? 'bg-green-500/20 text-green-400' :
            j.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
            j.status === 'failed' ? 'bg-red-500/20 text-red-400' :
            'bg-gray-500/20 text-gray-400'
          }`}>{j.status}</span>
        </div>
      ))}
    </div>
  );
}
