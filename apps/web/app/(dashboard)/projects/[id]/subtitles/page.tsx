'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

// =============================================================================
// Types
// =============================================================================

interface SubtitleTrack {
  id: string;
  project_id: string;
  format: string;
  storage_key: string;
  version: number;
  status: string;
  created_at: string;
}

interface SubtitleStatus {
  track_id: string | null;
  status: string;
  progress: number;
  message: string | null;
}

interface Project {
  id: string;
  brief?: {
    topic?: string;
  };
}

// =============================================================================
// Main Component
// =============================================================================

export default function SubtitlesPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [tracks, setTracks] = useState<SubtitleTrack[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState<SubtitleStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch project and tracks
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch project
        const projectRes = await fetch(`/api/projects/${id}`);
        if (projectRes.ok) {
          const projectData = await projectRes.json();
          setProject(projectData);
        }

        // Fetch subtitle tracks
        const tracksRes = await fetch(`/api/projects/${id}/subtitles`);
        if (tracksRes.ok) {
          const tracksData = await tracksRes.json();
          setTracks(tracksData);
        }

        // Fetch status
        const statusRes = await fetch(`/api/projects/${id}/subtitles/status`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setStatus(statusData);
        }
      } catch (err) {
        setError('Failed to load subtitles');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [id]);

  // Poll status while generating
  useEffect(() => {
    if (status?.status === 'processing' || status?.status === 'pending') {
      const interval = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/projects/${id}/subtitles/status`);
          if (statusRes.ok) {
            const data = await statusRes.json();
            setStatus(data);
            
            // Refresh tracks if completed
            if (data.status === 'generated') {
              const tracksRes = await fetch(`/api/projects/${id}/subtitles`);
              if (tracksRes.ok) {
                const tracksData = await tracksRes.json();
                setTracks(tracksData);
              }
            }
          }
        } catch (err) {
          // Ignore polling errors
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [id, status?.status]);

  // Generate subtitles
  async function handleGenerate() {
    setGenerating(true);
    setError(null);

    try {
      const res = await fetch(`/api/projects/${id}/subtitles/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_regenerate: false }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Generation failed');
      }

      const data = await res.json();
      setStatus({
        track_id: data.track_id,
        status: 'processing',
        progress: 0,
        message: data.message,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  // Download track
  async function handleDownload(track: SubtitleTrack) {
    try {
      const res = await fetch(`/api/projects/subtitles/${track.id}/download`);
      if (!res.ok) throw new Error('Download failed');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `subtitle_v${track.version}.srt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Download failed');
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <div className="animate-pulse text-[var(--fg-secondary)]">Đang tải…</div>
      </div>
    );
  }

  const isProcessing = status?.status === 'processing' || status?.status === 'pending';

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <a href={`/projects/${id}`} className="text-sm text-[var(--brand-400)] hover:underline">
            ← Back to Project
          </a>
          <span className="text-[var(--fg-tertiary)]">|</span>
          <a href={`/projects/${id}/render-config`} className="text-sm text-[var(--brand-400)] hover:underline">
            Render Config
          </a>
          <span className="text-[var(--fg-tertiary)]">|</span>
          <a href={`/projects/${id}/timeline-debug`} className="text-sm text-[var(--brand-400)] hover:underline">
            Timeline Debug
          </a>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          <span className="gradient-text">Subtitles / SRT</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Generate và download SRT subtitles từ voice lines.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}

      {/* Status Card */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Subtitle Generation</h2>
            <p className="text-sm text-[var(--fg-tertiary)] mt-1">
              {isProcessing
                ? 'Đang xử lý…'
                : status?.status === 'generated'
                  ? `Version ${tracks[0]?.version || 1} — Ready to download`
                  : 'Chưa có subtitles'}
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating || isProcessing}
            className="px-6 py-3 rounded-xl gradient-bg text-white font-semibold disabled:opacity-50"
          >
            {generating || isProcessing ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⟳</span>
                Generating…
              </span>
            ) : (
              'Generate Subtitles'
            )}
          </button>
        </div>

        {/* Progress Bar */}
        {isProcessing && (
          <div className="mt-4">
            <div className="h-2 rounded-full bg-[var(--surface)] overflow-hidden">
              <div
                className="h-full gradient-bg rounded-full transition-all duration-500"
                style={{ width: `${status?.progress || 50}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Subtitle Tracks */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-4">
          Subtitle Tracks ({tracks.length})
        </h2>

        {tracks.length === 0 ? (
          <div className="text-center py-8 text-[var(--fg-tertiary)]">
            <p>Chưa có subtitle track nào.</p>
            <p className="text-sm mt-1">Click "Generate Subtitles" để tạo SRT file.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tracks.map((track) => (
              <div
                key={track.id}
                className="flex items-center gap-4 p-4 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)]"
              >
                {/* Icon */}
                <div className="h-10 w-10 rounded-lg bg-[var(--brand-500)]/20 flex items-center justify-center text-[var(--brand-300)]">
                  📝
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Version {track.version}</span>
                    <span className="px-2 py-0.5 rounded text-xs bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                      {track.format.toUpperCase()}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      track.status === 'generated'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {track.status}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--fg-tertiary)] mt-1">
                    Created: {new Date(track.created_at).toLocaleString('vi-VN')}
                  </p>
                </div>

                {/* Download Button */}
                <button
                  onClick={() => handleDownload(track)}
                  disabled={track.status !== 'generated'}
                  className="px-4 py-2 rounded-lg bg-[var(--brand-500)]/20 text-[var(--brand-300)] text-sm font-medium disabled:opacity-50 hover:bg-[var(--brand-500)]/30"
                >
                  ⬇ Download .srt
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-3">Hướng dẫn</h2>
        <ol className="text-sm text-[var(--fg-secondary)] space-y-2 list-decimal list-inside">
          <li>Đảm bảo đã generate voice lines cho các scenes</li>
          <li>Click "Generate Subtitles" để tạo SRT file</li>
          <li>Download file .srt sau khi hoàn thành</li>
          <li>Upload file lên YouTube Studio khi upload video</li>
        </ol>
      </div>
    </div>
  );
}
