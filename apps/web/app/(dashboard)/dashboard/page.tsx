import { redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { JobCard } from '@/components/job-card';
import { IconDashboard, IconPlus } from '@/components/icons';

export default async function DashboardPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const response = await apiFetch('/api/jobs/recent', {}, token);
  const jobs = response.ok ? await response.json() : [];

  return (
    <div className="space-y-8 animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
            <IconDashboard size={14} /> Dashboard
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
            <span className="gradient-text">Hoạt động gần đây</span>
          </h1>
          <p className="text-[var(--fg-secondary)] max-w-xl">
            Theo dõi các dự án đang chạy và tiến độ xử lý của bạn.
          </p>
        </div>
        <Link
          href="/projects/new"
          className="btn-glow relative inline-flex items-center gap-2 px-5 h-11 rounded-xl text-sm font-semibold text-white"
        >
          <span className="relative inline-flex items-center gap-2 gradient-bg rounded-[10px] px-5 h-11">
            <IconPlus size={16} /> Dự án mới
          </span>
        </Link>
      </div>

      <div className="grid gap-4">
        {jobs.length === 0 ? (
          <div className="relative overflow-hidden rounded-3xl glass-strong p-12 text-center">
            <div
              aria-hidden
              className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-72 w-72 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl"
            />
            <p className="relative text-[var(--fg-secondary)]">Chưa có dự án nào — tạo dự án đầu tiên nhé.</p>
          </div>
        ) : (
          jobs.map((job: any, idx: number) => (
            <div
              key={job.id}
              className="animate-fade-up"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <JobCard job={job} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
