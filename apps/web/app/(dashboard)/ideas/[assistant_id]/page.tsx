import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { IdeasList } from '@/components/ideas/ideas-list';
import { RegenerateButton } from '@/components/ideas/regenerate-button';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export default async function IdeasPage({
  params,
}: {
  params: Promise<{ assistant_id: string }>;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const { assistant_id } = await params;

  // Fetch assistant
  const asstRes = await apiFetch(`/api/assistants/${assistant_id}`, {}, token);
  if (asstRes.status === 404) notFound();
  const assistant = await asstRes.json();

  // Fetch ideas
  const res = await apiFetch(`/api/ideas/${assistant_id}`, {}, token);
  const ideas: Idea[] = res.ok ? await res.json() : [];

  // Stats
  const stats = {
    total: ideas.length,
    topScore: ideas.length > 0 ? Math.max(...ideas.map((i) => i.gap_score)) : 0,
    avgScore: ideas.length > 0
      ? Math.round(ideas.reduce((sum, i) => sum + i.gap_score, 0) / ideas.length)
      : 0,
    highCount: ideas.filter((i) => i.confidence === 'high').length,
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <Link
        href={`/assistants/${assistant_id}`}
        className="text-blue-600 hover:underline"
      >
        ← Quay lại Assistant
      </Link>

      <div className="flex items-center justify-between mt-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold">
            Ideas: {assistant.channel_name}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {stats.total} ideas • Top: {stats.topScore} • Avg: {stats.avgScore} •{' '}
            {stats.highCount} HIGH confidence
          </p>
        </div>
        <RegenerateButton assistantId={assistant_id} />
      </div>

      {ideas.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border">
          <div className="text-6xl mb-4">💡</div>
          <h2 className="text-xl font-semibold mb-2">
            Chưa có Idea nào cho kênh này
          </h2>
          <p className="text-gray-500 mb-6">
            Generate Ideas từ Deep Analysis sẽ charge 5 credits
          </p>
          <RegenerateButton assistantId={assistant_id} />
        </div>
      ) : (
        <IdeasList ideas={ideas} assistantId={assistant_id} />
      )}
    </main>
  );
}
