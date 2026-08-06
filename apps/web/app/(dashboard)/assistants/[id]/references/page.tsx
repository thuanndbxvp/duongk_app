'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';

export default function ReferencesPage() {
  const { id } = useParams<{ id: string }>();
  const [videoIds, setVideoIds] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState('');

  async function handleIngest() {
    const ids = videoIds.split(',').map(s => s.trim()).filter(Boolean);
    if (ids.length === 0) { setError('Nhập ít nhất 1 video ID'); return; }
    setLoading(true); setError(''); setResult(null);

    try {
      const res = await fetch(`/api/assistants/${id}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_ids: ids }),
      });
      const data = await res.json();
      if (res.ok) {
        setResult(`✅ Đã enqueue ingest batch: ${data.batch_id} (${data.video_count} videos)`);
      } else {
        setError(data.detail || 'Ingest failed');
      }
    } catch { setError('Cannot connect'); }
    setLoading(false);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">📥 Import References</h1>
      <p className="text-sm text-[var(--fg-secondary)]">
        Nhập YouTube video IDs để ingest comments và phân tích audience insights.
      </p>

      <div className="glass-strong rounded-xl p-6 space-y-4">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Video IDs (phân cách bằng dấu phẩy)
        </label>
        <textarea
          value={videoIds}
          onChange={e => setVideoIds(e.target.value)}
          placeholder="dQw4w9WgXcQ, jNQXAC9IVRw"
          rows={3}
          className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]"
        />
        <button onClick={handleIngest} disabled={loading}
          className="w-full h-12 rounded-xl gradient-bg text-white font-semibold text-sm disabled:opacity-50">
          {loading ? 'Đang ingest...' : '🚀 Ingest Comments'}
        </button>

        {result && <p className="text-sm text-green-400">{result}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
    </div>
  );
}
