import Link from 'next/link';
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AssistantCard } from '@/components/assistant-card';

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
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Channel Assistants</h1>
          <p className="text-gray-500 mt-1">
            DNA và phong cách các kênh YouTube của bạn
          </p>
        </div>
        <Link
          href="/projects/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Tạo mới
        </Link>
      </div>

      {assistants.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border">
          <div className="text-6xl mb-4">📺</div>
          <h2 className="text-xl font-semibold mb-2">
            Bạn chưa có Channel Assistant nào
          </h2>
          <p className="text-gray-500 mb-6">
            Thu thập kênh YouTube để bắt đầu phân tích DNA
          </p>
          <Link
            href="/projects/new"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            📺 Tạo Channel Assistant mới
          </Link>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {assistants.length} Channel Assistant{assistants.length !== 1 ? 's' : ''}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {assistants.map((assistant) => (
              <AssistantCard key={assistant.id} assistant={assistant} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
