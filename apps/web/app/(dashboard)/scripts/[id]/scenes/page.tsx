'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';

// =============================================================================
// Types
// =============================================================================

interface SceneContract {
  schema_version: number;
  scene_id: string;
  scene_index: number;
  narration: string;
  visual_description: string;
  image_prompt: string;
  video_prompt: string;
  asset_type: string;
  estimated_duration: number;
  characters: string[];
  background: string;
  continuity_references: string[];
  status: string;
}

interface SceneListResponse {
  scenes: SceneContract[];
  total_duration_seconds: number;
  scene_count: number;
}

interface BreakdownStatus {
  status: string;
  progress: number;
  job_id?: string;
  error_message?: string;
}

// =============================================================================
// Main Component
// =============================================================================

export default function ScriptScenesPage() {
  const { id } = useParams<{ id: string }>();
  const [scenes, setScenes] = useState<SceneContract[]>([]);
  const [totalDuration, setTotalDuration] = useState(0);
  const [loading, setLoading] = useState(true);
  const [breaking, setBreaking] = useState(false);
  const [status, setStatus] = useState<BreakdownStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedScene, setSelectedScene] = useState<string | null>(null);

  // Fetch scenes
  const fetchScenes = useCallback(async () => {
    try {
      const res = await fetch(`/api/scripts/${id}/scenes`);
      if (res.ok) {
        const data: SceneListResponse = await res.json();
        setScenes(data.scenes);
        setTotalDuration(data.total_duration_seconds);
      }
    } catch (err) {
      setError('Failed to load scenes');
    }
  }, [id]);

  // Initial load
  useEffect(() => {
    setLoading(true);
    
    Promise.all([
      fetchScenes(),
      fetch(`/api/scripts/${id}/breakdown/status`)
        .then(r => r.ok ? r.json() : null)
        .then(data => data && setStatus(data)),
    ]).finally(() => setLoading(false));
  }, [id, fetchScenes]);

  // Poll status while breaking
  useEffect(() => {
    if (status?.status === 'processing' || status?.status === 'pending') {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/scripts/${id}/breakdown/status`);
          if (res.ok) {
            const data = await res.json();
            setStatus(data);
            
            if (data.status === 'completed') {
              fetchScenes();
            }
          }
        } catch (err) {
          // Ignore polling errors
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [id, status?.status, fetchScenes]);

  // Trigger breakdown
  async function handleBreakdown() {
    setBreaking(true);
    setError(null);

    try {
      const res = await fetch(`/api/scripts/${id}/breakdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_duration_minutes: 10 }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Breakdown failed');
      }

      const data = await res.json();
      setStatus({
        status: 'processing',
        progress: 0,
        job_id: data.job_id,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBreaking(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-12 text-center">
        <div className="animate-pulse text-[var(--fg-secondary)]">Đang tải scenes…</div>
      </div>
    );
  }

  const isProcessing = status?.status === 'processing' || status?.status === 'pending';
  const selectedSceneData = scenes.find(s => s.scene_id === selectedScene);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-up">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <a href={`/projects`} className="text-sm text-[var(--brand-400)] hover:underline">
            ← Back to Projects
          </a>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          <span className="gradient-text">Script Scene Breakdown</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Break script into scenes với AI-powered B-roll suggestions.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}

      {/* Stats Bar */}
      <div className="glass rounded-xl p-4 flex items-center gap-6">
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Total Duration</span>
          <p className="text-xl font-bold">{totalDuration.toFixed(1)}s</p>
        </div>
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Scenes</span>
          <p className="text-xl font-bold">{scenes.length}</p>
        </div>
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Schema</span>
          <p className="text-xl font-bold">v{scenes[0]?.schema_version || 1}</p>
        </div>
        <div className="ml-auto flex gap-3">
          <button
            onClick={handleBreakdown}
            disabled={breaking || isProcessing}
            className="px-6 py-3 rounded-xl gradient-bg text-white font-semibold disabled:opacity-50"
          >
            {breaking || isProcessing ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⟳</span>
                Breaking down…
              </span>
            ) : (
              '🔄 Break Script into Scenes'
            )}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {isProcessing && (
        <div className="glass rounded-xl p-4">
          <div className="flex justify-between text-sm mb-2">
            <span>Processing scenes…</span>
            <span>{status?.progress || 0}%</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--surface)] overflow-hidden">
            <div
              className="h-full gradient-bg rounded-full transition-all duration-500"
              style={{ width: `${status?.progress || 50}%` }}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Scene List */}
        <div className="lg:col-span-2 glass rounded-2xl p-4">
          <h2 className="text-lg font-semibold mb-4">Scenes ({scenes.length})</h2>
          
          {scenes.length === 0 ? (
            <div className="text-center py-12 text-[var(--fg-tertiary)]">
              <p>Chưa có scenes nào.</p>
              <p className="mt-1">Click "Break Script into Scenes" để bắt đầu.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {scenes.map((scene) => (
                <div
                  key={scene.scene_id}
                  onClick={() => setSelectedScene(scene.scene_id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedScene === scene.scene_id
                      ? 'border-[var(--brand-500)] bg-[var(--brand-500)]/10'
                      : 'border-[var(--glass-border)] bg-[var(--surface)] hover:border-[var(--brand-500)]/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Scene Number */}
                    <div className="h-8 w-8 rounded-lg bg-[var(--brand-500)]/20 flex items-center justify-center text-[var(--brand-300)] font-bold text-sm">
                      {scene.scene_index + 1}
                    </div>

                    {/* Scene Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded bg-[var(--brand-500)]/20 text-[var(--brand-300)] text-xs">
                          {scene.asset_type}
                        </span>
                        <span className="text-sm font-mono text-[var(--fg-tertiary)]">
                          {scene.estimated_duration.toFixed(1)}s
                        </span>
                      </div>
                      <p className="text-sm line-clamp-2">
                        {scene.narration.slice(0, 100)}
                        {scene.narration.length > 100 && '…'}
                      </p>
                    </div>
                  </div>

                  {/* Timeline Bar */}
                  <div className="mt-3 h-1.5 rounded-full bg-[var(--surface)] overflow-hidden">
                    <div
                      className="h-full gradient-bg rounded-full"
                      style={{ width: `${(scene.estimated_duration / totalDuration) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Scene Detail Panel */}
        <div className="glass rounded-2xl p-4">
          <h2 className="text-lg font-semibold mb-4">
            {selectedSceneData ? `Scene ${selectedSceneData.scene_index + 1}` : 'Scene Details'}
          </h2>

          {selectedSceneData ? (
            <div className="space-y-4">
              {/* Narration */}
              <div>
                <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Narration</label>
                <p className="text-sm mt-1 bg-[var(--surface)] rounded-lg p-3">
                  {selectedSceneData.narration}
                </p>
              </div>

              {/* Visual Description */}
              <div>
                <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Visual Description</label>
                <p className="text-sm mt-1 bg-[var(--surface)] rounded-lg p-3">
                  {selectedSceneData.visual_description || '—'}
                </p>
              </div>

              {/* Image Prompt */}
              <div>
                <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Image Prompt</label>
                <div className="mt-1">
                  <textarea
                    value={selectedSceneData.image_prompt}
                    readOnly
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-xs resize-none font-mono"
                  />
                  <button
                    onClick={() => navigator.clipboard.writeText(selectedSceneData.image_prompt)}
                    className="mt-1 text-xs text-[var(--brand-400)] hover:underline"
                  >
                    📋 Copy prompt
                  </button>
                </div>
              </div>

              {/* Characters */}
              {selectedSceneData.characters.length > 0 && (
                <div>
                  <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Characters</label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedSceneData.characters.map((char, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-[var(--surface)] text-xs">
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Background */}
              {selectedSceneData.background && (
                <div>
                  <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Background</label>
                  <p className="text-sm mt-1">{selectedSceneData.background}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-3 border-t border-[var(--glass-border)]">
                <p className="text-xs text-[var(--fg-tertiary)] font-mono">
                  ID: {selectedSceneData.scene_id}
                </p>
                <p className="text-xs text-[var(--fg-tertiary)] font-mono">
                  Status: {selectedSceneData.status}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-[var(--fg-tertiary)]">
              <p>Click on a scene to see details</p>
            </div>
          )}
        </div>
      </div>

      {/* Timeline Bar */}
      {scenes.length > 0 && (
        <div className="glass rounded-2xl p-4">
          <h3 className="text-sm font-semibold mb-3">Timeline</h3>
          <div className="h-8 rounded-lg bg-[var(--surface)] overflow-hidden flex">
            {scenes.map((scene, idx) => (
              <div
                key={scene.scene_id}
                onClick={() => setSelectedScene(scene.scene_id)}
                title={`Scene ${idx + 1}: ${scene.estimated_duration.toFixed(1)}s`}
                className={`h-full border-r border-[var(--surface)] cursor-pointer hover:opacity-80 transition-opacity ${
                  selectedScene === scene.scene_id ? 'gradient-bg' : 'bg-[var(--brand-500)]/30'
                }`}
                style={{ width: `${(scene.estimated_duration / totalDuration) * 100}%` }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-1 text-xs text-[var(--fg-tertiary)]">
            <span>0s</span>
            <span>{totalDuration.toFixed(1)}s</span>
          </div>
        </div>
      )}
    </div>
  );
}
