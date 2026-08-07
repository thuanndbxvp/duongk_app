import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AnalysisTabs } from '@/components/analysis/analysis-tabs';
import { ReanalyzeButton } from '@/components/analysis/reanalyze-button';

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

  // Fetch 6 analysis sub-endpoints in parallel (Phase 2 fix)
  const [nlpRes, llmRes, detRes, insRes, thumbRes, outRes] = await Promise.all([
    apiFetch(`/api/analysis/${assistant_id}/nlp`, {}, token),
    apiFetch(`/api/analysis/${assistant_id}/llm`, {}, token),
    apiFetch(`/api/analysis/${assistant_id}/deterministic`, {}, token),
    apiFetch(`/api/analysis/${assistant_id}/insights`, {}, token),
    apiFetch(`/api/analysis/${assistant_id}/thumbnail`, {}, token),
    apiFetch(`/api/analysis/${assistant_id}/output`, {}, token),
  ]);

  const [nlp, llm, deterministic, insights, thumbnail, output] = await Promise.all([
    nlpRes.ok ? nlpRes.json() : null,
    llmRes.ok ? llmRes.json() : null,
    detRes.ok ? detRes.json() : null,
    insRes.ok ? insRes.json() : null,
    thumbRes.ok ? thumbRes.json() : null,
    outRes.ok ? outRes.json() : null,
  ]);

  // Empty state if not analyzed yet
  if (!nlp && !llm && !deterministic && !insights && !thumbnail && !output) {
    return (
      <main className="container mx-auto p-8 max-w-3xl">
        <Link
          href={`/assistants/${assistant_id}`}
          className="text-[var(--brand-300)] hover:text-[var(--brand-400)]"
        >
          ← Quay lại Assistant
        </Link>
        <div className="text-center py-16 glass rounded-2xl mt-6">
          <div className="text-6xl mb-4">🧠</div>
          <h1 className="text-2xl font-bold mb-2">
            Chưa chạy Deep Analysis cho {assistant.channel_name}
          </h1>
          <p className="text-[var(--fg-tertiary)] mb-6">
            Phân tích 14 outputs sẽ charge 50 credits (~2-3 phút)
          </p>
          <ReanalyzeButton assistantId={assistant_id} />
        </div>
      </main>
    );
  }

  const data = { nlp, llm, deterministic, insights, thumbnail, output };

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <Link
        href={`/assistants/${assistant_id}`}
        className="text-[var(--brand-300)] hover:text-[var(--brand-400)]"
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
