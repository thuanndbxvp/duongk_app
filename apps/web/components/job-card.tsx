'use client';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  created_at: string;
}

const STATUS_META: Record<
  string,
  { label: string; text: string; bar: string; pulse: boolean }
> = {
  pending: { label: 'Đang chờ', text: 'text-[var(--warning)]', bar: 'bg-[var(--warning)]', pulse: false },
  running: { label: 'Đang chạy', text: 'text-[var(--brand-300)]', bar: 'bg-gradient-to-r from-[var(--brand-500)] to-[#ec4899]', pulse: true },
  succeeded: { label: 'Hoàn tất', text: 'text-[var(--success)]', bar: 'bg-[var(--success)]', pulse: false },
  failed: { label: 'Thất bại', text: 'text-[var(--danger)]', bar: 'bg-[var(--danger)]', pulse: false },
};

export function JobCard({ job }: { job: Job }) {
  const meta = STATUS_META[job.status] ?? STATUS_META.pending;
  const progress = Math.max(0, Math.min(100, job.progress ?? 0));

  return (
    <a
      href={`/jobs/${job.id}`}
      className="group relative block rounded-2xl p-5 glass glass-hover transition-all duration-300 overflow-hidden"
    >
      <span
        aria-hidden
        className="pointer-events-none absolute -top-12 -right-12 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-0 blur-3xl group-hover:opacity-20 transition-opacity duration-500"
      />

      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="font-semibold text-base text-white capitalize truncate">
            {job.task_type.replace(/_/g, ' ')}
          </h3>
          <p className="text-sm text-[var(--fg-tertiary)] tabular-nums">
            {new Date(job.created_at).toLocaleString('vi-VN')}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${meta.text}`}>
            {meta.pulse && (
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--brand-400)] animate-pulse-glow" />
            )}
            {meta.label}
          </span>
          <span className="text-xs text-[var(--fg-tertiary)] tabular-nums">{progress}%</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative mt-4 h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
        <div
          className={`h-full rounded-full ${meta.bar} transition-all duration-500`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </a>
  );
}
