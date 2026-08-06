'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { InsightCard } from '@/components/insight-card';

interface Insight {
  id: string;
  title: string;
  body: string;
  evidence_comment_ids: string[];
  opportunity_score: number | null;
  status: string;
  created_at: string;
}

export default function InsightsPage() {
  const { id } = useParams<{ id: string }>();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetch(`/api/assistants/${id}/insights`)
      .then(r => r.json())
      .then(data => setInsights(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleApprove(insightId: string) {
    await fetch(`/api/insights/${insightId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision: 'approved' }),
    });
    setInsights(prev => prev.map(i => i.id === insightId ? { ...i, status: 'approved' } : i));
  }

  async function handleReject(insightId: string) {
    await fetch(`/api/insights/${insightId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision: 'rejected' }),
    });
    setInsights(prev => prev.map(i => i.id === insightId ? { ...i, status: 'rejected' } : i));
  }

  async function handleToProject(insightId: string) {
    const res = await fetch(`/api/insights/${insightId}/to-project`, { method: 'POST' });
    const data = await res.json();
    if (data.project_id) {
      window.location.href = `/projects/${data.project_id}`;
    }
  }

  const filtered = filter === 'all' ? insights : insights.filter(i => i.status === filter);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">💡 Channel Insights</h1>
        <div className="flex gap-1 p-1 rounded-lg bg-white/[0.04]">
          {['all', 'pending', 'approved', 'applied', 'rejected'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-md transition ${filter === f ? 'gradient-bg text-white' : 'text-[var(--fg-tertiary)]'}`}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-[var(--fg-secondary)] animate-pulse">Đang tải insights...</p>
      ) : filtered.length === 0 ? (
        <p className="text-[var(--fg-tertiary)] text-center py-12">Chưa có insight nào. Hãy ingest comments trước.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map(insight => (
            <InsightCard key={insight.id} insight={insight}
              onApprove={handleApprove} onReject={handleReject} onToProject={handleToProject} />
          ))}
        </div>
      )}
    </div>
  );
}
