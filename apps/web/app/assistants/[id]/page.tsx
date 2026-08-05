import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '../../../../../lib/api-client';
import { getAccessToken } from '../../../../../lib/auth';
import { AssistantActions } from '../../../../../components/assistant-actions';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_id: string;
  channel_subscribers: number;
  total_videos_collected: number;
  quality_videos_count: number;
  viral_videos_count: number;
  status: string;
  has_analysis: boolean;
  scripts_count: number;
  created_at: string;
}

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  created_at: string;
}

export default async function AssistantDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const { id } = await params;

  // Fetch assistant
  const res = await apiFetch(`/api/assistants/${id}`, {}, token);
  if (res.status === 404) notFound();
  if (!res.ok) redirect('/assistants');

  const assistant: Assistant = await res.json();

  // Fetch recent jobs (optional)
  const jobsRes = await apiFetch(`/api/jobs?assistant_id=${id}&limit=5`, {}, token);
  const recentJobs: Job[] = jobsRes.ok ? await jobsRes.json() : [];

  const formatSubs = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <div className="flex items-center mb-6">
        <Link href="/assistants" className="text-blue-600 hover:underline">
          ← Quay lại danh sách
        </Link>
      </div>

      {/* Header */}
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
        <div className="flex items-start gap-6">
          <img
            src={assistant.channel_thumbnail || '/placeholder.png'}
            alt={assistant.channel_name}
            className="w-24 h-24 rounded-full object-cover"
          />
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">{assistant.channel_name}</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Subscribers</div>
                <div className="font-semibold">
                  {formatSubs(assistant.channel_subscribers)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Videos</div>
                <div className="font-semibold">
                  {assistant.total_videos_collected}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Viral</div>
                <div className="font-semibold text-orange-600">
                  {assistant.viral_videos_count}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Status</div>
                <div className="font-semibold capitalize">{assistant.status}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Hành động</h2>
        <AssistantActions
          assistantId={assistant.id}
          hasAnalysis={assistant.has_analysis}
          hasScripts={assistant.scripts_count > 0}
        />
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h2 className="text-lg font-semibold mb-4">Jobs gần đây</h2>
        {recentJobs.length === 0 ? (
          <p className="text-gray-500 italic">Chưa có job nào.</p>
        ) : (
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <Link
                key={job.id}
                href={`/jobs/${job.id}`}
                className="block p-3 border rounded hover:bg-gray-50"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium capitalize">
                      {job.task_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleString('vi-VN')}
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="px-2 py-1 bg-gray-100 rounded-full capitalize">
                      {job.status} ({job.progress}%)
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
