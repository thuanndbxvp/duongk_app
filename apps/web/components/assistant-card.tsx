import Link from 'next/link';
import { IconBrain, IconArrowRight, IconCheck, IconAlert } from '@/components/icons';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_subscribers: number;
  total_videos_collected: number;
  viral_videos_count: number;
  status: 'collecting' | 'ready' | 'failed';
  has_analysis: boolean;
  scripts_count: number;
  last_job_at: string | null;
  created_at: string;
}

const STATUS_META: Record<
  Assistant['status'],
  { label: string; dot: string; text: string; icon: React.ReactNode }
> = {
  ready: {
    label: 'Sẵn sàng',
    dot: 'bg-[var(--success)]',
    text: 'text-[var(--success)]',
    icon: <IconCheck size={12} />,
  },
  collecting: {
    label: 'Đang thu thập',
    dot: 'bg-[var(--brand-400)] animate-pulse',
    text: 'text-[var(--brand-300)]',
    icon: <span className="inline-block h-2 w-2 rounded-full bg-[var(--brand-400)] animate-pulse-glow" />,
  },
  failed: {
    label: 'Lỗi',
    dot: 'bg-[var(--danger)]',
    text: 'text-[var(--danger)]',
    icon: <IconAlert size={12} />,
  },
};

export function AssistantCard({ assistant }: { assistant: Assistant }) {
  const meta = STATUS_META[assistant.status] ?? STATUS_META.collecting;

  const formatSubs = (n: number): string => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <Link
      href={`/assistants/${assistant.id}`}
      className="group relative block rounded-2xl p-5 glass glass-hover hover:-translate-y-0.5 transition-all duration-300 overflow-hidden"
    >
      {/* glow on hover */}
      <span
        aria-hidden
        className="pointer-events-none absolute -top-12 -right-12 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-0 blur-3xl group-hover:opacity-25 transition-opacity duration-500"
      />

      <div className="relative flex items-start gap-4">
        <div className="relative">
          <img
            src={assistant.channel_thumbnail || '/placeholder.png'}
            alt={assistant.channel_name}
            className="w-14 h-14 rounded-2xl object-cover ring-1 ring-[var(--glass-border-strong)]"
          />
          {assistant.has_analysis && (
            <span
              className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full gradient-bg flex items-center justify-center ring-2 ring-[var(--bg-base)]"
              aria-label="Đã phân tích"
            >
              <IconBrain size={12} className="text-white" />
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-base text-white truncate">{assistant.channel_name}</h3>
          <p className="text-sm text-[var(--fg-tertiary)] tabular-nums">
            {formatSubs(assistant.channel_subscribers)} subscribers
          </p>
        </div>
      </div>

      <div className="relative mt-5 grid grid-cols-3 gap-2 text-center">
        <Stat value={assistant.total_videos_collected} label="videos" tone="default" />
        <Stat value={assistant.viral_videos_count} label="viral" tone="viral" />
        <Stat value={assistant.scripts_count} label="scripts" tone="brand" />
      </div>

      <div className="relative mt-5 pt-4 border-t border-[var(--divider)] flex items-center justify-between">
        <span
          className={`inline-flex items-center gap-1.5 text-xs font-semibold ${meta.text}`}
        >
          {meta.dot && <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />}
          {meta.icon}
          {meta.label}
        </span>
        <span className="inline-flex items-center gap-1 text-xs text-[var(--fg-tertiary)] group-hover:text-[var(--brand-300)] transition-colors">
          Mở <IconArrowRight size={12} />
        </span>
      </div>
    </Link>
  );
}

function Stat({
  value,
  label,
  tone,
}: {
  value: number;
  label: string;
  tone: 'default' | 'viral' | 'brand';
}) {
  const colors = {
    default: 'text-white',
    viral: 'text-amber-300',
    brand: 'text-[var(--brand-300)]',
  };
  return (
    <div className="rounded-xl bg-white/[0.02] py-2.5">
      <div className={`text-xl font-bold tabular-nums ${colors[tone]}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-[var(--fg-tertiary)] mt-0.5">
        {label}
      </div>
    </div>
  );
}
