'use client';

import { useEffect, useState } from 'react';

interface Props { projectId: string; }

interface Anchor { id: string; character_name: string; asset_id: string | null; provider: string; anchor_strength: number; is_approved: boolean; }

export function CharacterLab({ projectId }: Props) {
  const [anchors, setAnchors] = useState<Anchor[]>([]);
  const [coverage, setCoverage] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  async function fetchData() {
    setLoading(true);
    try {
      const [charRes, covRes] = await Promise.all([
        fetch(`/api/projects/${projectId}/lab/characters`),
        fetch(`/api/projects/${projectId}/lab/coverage`),
      ]);
      setAnchors(await charRes.json());
      const cov = await covRes.json();
      setCoverage(cov.coverage_pct || 0);
    } catch {}
    setLoading(false);
  }

  async function handleStart() {
    await fetch(`/api/projects/${projectId}/lab/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    setTimeout(fetchData, 3000);
  }

  async function handleApprove() {
    await fetch(`/api/projects/${projectId}/lab/approve`, { method: 'POST' });
    fetchData();
  }

  useEffect(() => { fetchData(); }, [projectId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">👤 Character Lab</h3>
        <div className="flex gap-2 items-center">
          <span className={`text-xs px-2 py-0.5 rounded ${coverage >= 1 ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
            Coverage: {(coverage * 100).toFixed(0)}%
          </span>
          <button onClick={handleStart} className="px-3 py-1.5 rounded-lg gradient-bg text-white text-xs font-medium">Start Lab</button>
          <button onClick={handleApprove} disabled={coverage < 1}
            className="px-3 py-1.5 rounded-lg bg-green-500/20 text-green-400 text-xs font-medium disabled:opacity-30">Approve</button>
        </div>
      </div>

      {loading ? <p className="text-sm text-[var(--fg-secondary)]">Loading...</p> :
        anchors.length === 0 ? <p className="text-sm text-[var(--fg-tertiary)] text-center py-8">No character anchors yet. Start a lab session.</p> :
        <div className="grid grid-cols-3 gap-3">
          {anchors.map(a => (
            <div key={a.id} className={`glass rounded-xl p-3 text-center ${a.is_approved ? 'border border-green-500/30' : ''}`}>
              <div className="text-3xl mb-2">👤</div>
              <p className="text-xs font-medium">{a.character_name}</p>
              <p className="text-[10px] text-[var(--fg-tertiary)]">{a.provider} · {Math.round(a.anchor_strength * 100)}%</p>
              {a.is_approved && <span className="text-[10px] text-green-400">✓ Approved</span>}
            </div>
          ))}
        </div>
      }
    </div>
  );
}
