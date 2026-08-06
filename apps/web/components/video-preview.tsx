'use client';

import { useState, useEffect } from 'react';

interface Props {
  projectId: string;
}

interface RenderJob {
  id: string;
  job_type: string;
  status: string;
  progress: number;
  error_code?: string;
  output_asset_id?: string;
  finished_at?: string;
}

export function VideoPreview({ projectId }: Props) {
  const [jobs, setJobs] = useState<RenderJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function fetchExports() {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/exports`);
      const data = await res.json();
      setJobs(Array.isArray(data) ? data : []);
    } catch { setError('Cannot fetch exports'); }
    setLoading(false);
  }

  async function startRender(kind: 'draft' | 'final') {
    setLoading(true); setError('');
    try {
      // Get timeline first
      const tlRes = await fetch(`/api/projects/${projectId}/timeline`);
      if (!tlRes.ok) { setError('No timeline compiled yet'); setLoading(false); return; }
      const tl = await tlRes.json();

      const res = await fetch(`/api/projects/${projectId}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind, timeline_id: tl.id }),
      });
      if (res.ok) {
        await fetchExports();
        // Poll for updates
        const job = await res.json();
        pollJob(job.render_job_id);
      } else {
        const err = await res.json();
        setError(err.detail || 'Render failed');
      }
    } catch { setError('Cannot start render'); }
    setLoading(false);
  }

  async function pollJob(jobId: string) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        const job: RenderJob = await res.json();
        setJobs(prev => prev.map(j => j.id === job.id ? job : j));
        if (['success', 'failed', 'cancelled'].includes(job.status)) {
          clearInterval(interval);
        }
      } catch { clearInterval(interval); }
    }, 3000);
  }

  useEffect(() => { fetchExports(); }, [projectId]);

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <button onClick={() => startRender('draft')} disabled={loading}
          className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
          🎬 Render Draft (720p)
        </button>
        <button onClick={() => startRender('final')} disabled={loading}
          className="px-4 py-2 rounded-lg bg-white/[0.06] border border-[var(--glass-border)] text-white text-sm font-medium disabled:opacity-50">
          🎥 Render Final (1080p)
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="space-y-3">
        {jobs.map(job => (
          <div key={job.id} className="glass-strong rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{job.job_type === 'draft' ? '🎬 Draft' : '🎥 Final'}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                job.status === 'success' ? 'bg-green-500/20 text-green-400' :
                job.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                job.status === 'cancelled' ? 'bg-yellow-500/20 text-yellow-400' :
                job.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>{job.status}</span>
            </div>
            {job.status === 'running' && (
              <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                <div className="h-full gradient-bg transition-all" style={{ width: `${(job.progress || 0) * 100}%` }} />
              </div>
            )}
            {job.status === 'success' && job.output_asset_id && (
              <a href={`/api/assets/${job.output_asset_id}`}
                className="text-xs text-[var(--brand-400)] hover:underline">
                📥 Download
              </a>
            )}
            {job.error_code && <p className="text-xs text-red-400">{job.error_code}</p>}
          </div>
        ))}
        {!loading && jobs.length === 0 && (
          <p className="text-sm text-[var(--fg-tertiary)] text-center py-8">Chưa có video nào được render.</p>
        )}
      </div>
    </div>
  );
}
