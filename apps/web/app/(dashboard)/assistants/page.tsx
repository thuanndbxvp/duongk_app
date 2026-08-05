import Link from 'next/link';
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AssistantCard } from '@/components/assistant-card';
import { IconChannels, IconPlus } from '@/components/icons';

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

export default async function AssistantsPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const response = await apiFetch('/api/assistants', {}, token);
  const assistants: Assistant[] = response.ok ? await response.json() : [];

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
            <IconChannels size={14} /> Channels
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
            <span className="gradient-text">Channel Assistants</span>
          </h1>
          <p className="text-[var(--fg-secondary)] max-w-xl">
            DNA phong cách các kênh YouTube của bạn — phân tích viral và sinh script theo cùng DNA.
          </p>
        </div>
        <Link
          href="/projects/new"
          className="btn-glow relative inline-flex items-center gap-2 px-5 h-11 rounded-xl text-sm font-semibold text-white"
        >
          <span className="relative inline-flex items-center gap-2 gradient-bg rounded-[10px] px-5 h-11">
            <IconPlus size={16} /> Tạo mới
          </span>
        </Link>
      </div>

      {assistants.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-[var(--fg-tertiary)]">
              <span className="text-white font-semibold tabular-nums">{assistants.length}</span>{' '}
              Channel Assistant{assistants.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {assistants.map((assistant, idx) => (
              <div
                key={assistant.id}
                className="animate-fade-up"
                style={{ animationDelay: `${idx * 40}ms` }}
              >
                <AssistantCard assistant={assistant} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="relative overflow-hidden rounded-3xl glass-strong p-12 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-72 w-72 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl"
      />
      <div className="relative">
        <div className="mx-auto h-20 w-20 rounded-2xl gradient-bg flex items-center justify-center mb-6 btn-glow">
          <IconChannels size={32} className="text-white relative" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Bạn chưa có Channel Assistant</h2>
        <p className="text-[var(--fg-secondary)] max-w-md mx-auto mb-8">
          Thu thập kênh YouTube để AppDK phân tích DNA phong cách, viral patterns và sinh script theo đúng chất kênh.
        </p>
        <Link
          href="/projects/new"
          className="btn-glow relative inline-flex items-center gap-2 px-6 h-12 rounded-xl text-sm font-semibold text-white"
        >
          <span className="relative inline-flex items-center gap-2 gradient-bg rounded-[10px] px-6 h-12">
            <IconPlus size={16} /> Tạo Channel Assistant mới
          </span>
        </Link>
      </div>
    </div>
  );
}
