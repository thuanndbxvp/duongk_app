import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { JobCard } from '@/components/job-card';

export default async function DashboardPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const response = await apiFetch('/api/jobs/recent', {}, token);
  let jobs = [];
  if (response.ok) {
    jobs = await response.json();
  }

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-4">
          <form action="/api/auth/logout" method="POST">
            <button type="submit" className="text-sm text-red-600 hover:underline">
              Đăng xuất
            </button>
          </form>
          <a href="/projects/new" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            + Dự án mới
          </a>
        </div>
      </div>

      <div className="grid gap-4">
        {jobs.length === 0 ? (
          <p className="text-gray-500">Chưa có dự án nào.</p>
        ) : (
          jobs.map((job: any) => (
            <JobCard key={job.id} job={job} />
          ))
        )}
      </div>
    </main>
  );
}
