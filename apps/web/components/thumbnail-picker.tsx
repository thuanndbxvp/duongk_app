'use client';

import { useState, useEffect } from 'react';

interface Props { projectId: string; }

interface Candidate {
  id: string;
  asset_id: string;
  score: number | null;
  provider: string;
  selected: boolean;
}

export function ThumbnailPicker({ projectId }: Props) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  async function fetchCandidates() {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/thumbnail/candidates`);
      const data = await res.json();
      setCandidates(Array.isArray(data) ? data : []);
    } catch {}
    setLoading(false);
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      await fetch(`/api/projects/${projectId}/thumbnail/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'gemini', count: 3 }),
      });
      setTimeout(fetchCandidates, 3000);
    } catch {}
    setGenerating(false);
  }

  async function handleSelect(candidateId: string) {
    await fetch(`/api/projects/${projectId}/thumbnail/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_id: candidateId }),
    });
    fetchCandidates();
  }

  useEffect(() => { fetchCandidates(); }, [projectId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🎨 Thumbnails</h3>
        <button onClick={handleGenerate} disabled={generating}
          className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
          {generating ? 'Đang tạo...' : '🤖 Generate'}
        </button>
      </div>

      {loading && <p className="text-sm text-[var(--fg-secondary)]">Đang tải...</p>}

      <div className="grid grid-cols-3 gap-4">
        {candidates.map(c => (
          <div key={c.id}
            onClick={() => handleSelect(c.id)}
            className={`relative rounded-xl overflow-hidden border-2 cursor-pointer transition hover:border-[var(--brand-400)]/50 ${
              c.selected ? 'border-[var(--brand-400)] ring-2 ring-[var(--brand-400)]/30' : 'border-transparent'
            }`}
          >
            <div className="aspect-video bg-white/[0.04] flex items-center justify-center text-4xl">
              🖼️
            </div>
            <div className="p-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--fg-tertiary)]">{c.provider}</span>
                {c.score && <span className="text-xs text-green-400">{(c.score * 100).toFixed(0)}%</span>}
              </div>
              {c.selected && <span className="text-xs text-[var(--brand-400)] font-medium">✅ Selected</span>}
            </div>
          </div>
        ))}
      </div>

      {!loading && candidates.length === 0 && (
        <p className="text-sm text-[var(--fg-tertiary)] text-center py-4">Chưa có thumbnail. Nhấn Generate để tạo.</p>
      )}
    </div>
  );
}
