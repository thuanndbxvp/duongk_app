import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '../../../../../lib/api-client';
import { getAccessToken } from '../../../../../lib/auth';
import { AnalysisTabs } from '../../../../../components/analysis/analysis-tabs';
import { ReanalyzeButton } from '../../../../../components/analysis/reanalyze-button';

export default async function AnalysisPage({
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

  // Fetch analysis
  const res = await apiFetch(`/api/analysis/${assistant_id}`, {}, token);

  // Empty state if not analyzed yet
  if (res.status === 404) {
    return (
      <main className="container mx-auto p-8 max-w-3xl">
        <Link
          href={`/assistants/${assistant_id}`}
          className="text-blue-600 hover:underline"
        >
          ← Quay lại Assistant
        </Link>
        <div className="text-center py-16 bg-white rounded-lg border mt-6">
          <div className="text-6xl mb-4">🧠</div>
          <h1 className="text-2xl font-bold mb-2">
            Chưa chạy Deep Analysis cho {assistant.channel_name}
          </h1>
          <p className="text-gray-500 mb-6">
            Phân tích 14 outputs sẽ charge 50 credits (~2-3 phút)
          </p>
          <ReanalyzeButton assistantId={assistant_id} />
        </div>
      </main>
    );
  }

  if (!res.ok) {
    return (
      <main className="container mx-auto p-8">
        <p className="text-red-600">Failed to load analysis.</p>
      </main>
    );
  }

  const data = await res.json();

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <Link
        href={`/assistants/${assistant_id}`}
        className="text-blue-600 hover:underline"
      >
        ← Quay lại Assistant
      </Link>
      
      <div className="flex items-center justify-between mt-4 mb-6">
        <h1 className="text-3xl font-bold">
          Deep Analysis: {assistant.channel_name}
        </h1>
        <ReanalyzeButton assistantId={assistant_id} />
      </div>

      <AnalysisTabs data={data} />
    </main>
  );
}
