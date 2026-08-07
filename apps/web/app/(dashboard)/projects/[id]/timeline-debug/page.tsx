'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';

// =============================================================================
// Types
// =============================================================================

interface TimelineScene {
  id: string;
  order: number;
  duration_seconds: number;
  voice_line?: {
    text: string;
    audio_url?: string;
    status?: string;
  };
  visual?: {
    type: 'text' | 'image' | 'video' | 'slideshow';
    content?: string;
    asset_url?: string;
  };
  transition?: string;
  metadata?: Record<string, any>;
}

interface TimelineModel {
  version: string;
  project_id: string;
  total_duration_seconds: number;
  scenes: TimelineScene[];
  metadata?: {
    created_at?: string;
    updated_at?: string;
    version?: string;
  };
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

export default function TimelineDebugPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [timeline, setTimeline] = useState<TimelineModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState('');

  // Fetch project and timeline
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch project
        const projectRes = await fetch(`/api/projects/${id}`);
        if (projectRes.ok) {
          const projectData = await projectRes.json();
          setProject(projectData);
        }

        // Fetch timeline
        const timelineRes = await fetch(`/api/projects/${id}/timeline`);
        if (timelineRes.ok) {
          const timelineData = await timelineRes.json();
          setTimeline(timelineData);
          setJsonText(JSON.stringify(timelineData, null, 2));
        } else {
          // Init empty timeline if not exists
          const empty: TimelineModel = {
            version: '1.0',
            project_id: id,
            total_duration_seconds: 0,
            scenes: [],
          };
          setTimeline(empty);
          setJsonText(JSON.stringify(empty, null, 2));
        }
      } catch (err) {
        setError('Failed to load timeline');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [id]);

  // Save timeline
  const handleSave = useCallback(async () => {
    if (!timeline) return;

    setSaving(true);
    setError(null);

    try {
      const res = await fetch(`/api/projects/${id}/timeline`, {
        method: jsonMode ? 'PUT' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(timeline),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Save failed');
      }

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }, [timeline, id, jsonMode]);

  // Parse JSON mode
  const handleJsonChange = useCallback((text: string) => {
    setJsonText(text);
    try {
      const parsed = JSON.parse(text);
      setTimeline(parsed);
      setError(null);
    } catch (e) {
      setError('Invalid JSON');
    }
  }, []);

  // Add scene
  const addScene = useCallback(() => {
    if (!timeline) return;

    const newScene: TimelineScene = {
      id: `scene_${Date.now()}`,
      order: timeline.scenes.length + 1,
      duration_seconds: 10,
      voice_line: { text: '' },
      visual: { type: 'text', content: '' },
    };

    setTimeline({
      ...timeline,
      scenes: [...timeline.scenes, newScene],
      total_duration_seconds: timeline.total_duration_seconds + 10,
    });
  }, [timeline]);

  // Delete scene
  const deleteScene = useCallback((sceneId: string) => {
    if (!timeline) return;

    const newScenes = timeline.scenes
      .filter(s => s.id !== sceneId)
      .map((s, i) => ({ ...s, order: i + 1 }));

    const newTotal = newScenes.reduce((sum, s) => sum + (s.duration_seconds || 0), 0);

    setTimeline({
      ...timeline,
      scenes: newScenes,
      total_duration_seconds: newTotal,
    });
    setSelectedScene(null);
  }, [timeline]);

  // Update scene
  const updateScene = useCallback((sceneId: string, updates: Partial<TimelineScene>) => {
    if (!timeline) return;

    const newScenes = timeline.scenes.map(s => {
      if (s.id === sceneId) {
        return { ...s, ...updates };
      }
      return s;
    });

    const newTotal = newScenes.reduce((sum, s) => sum + (s.duration_seconds || 0), 0);

    setTimeline({
      ...timeline,
      scenes: newScenes,
      total_duration_seconds: newTotal,
    });
  }, [timeline]);

  // Reorder scenes
  const moveScene = useCallback((sceneId: string, direction: 'up' | 'down') => {
    if (!timeline) return;

    const idx = timeline.scenes.findIndex(s => s.id === sceneId);
    if (idx === -1) return;

    const newIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (newIdx < 0 || newIdx >= timeline.scenes.length) return;

    const newScenes = [...timeline.scenes];
    [newScenes[idx], newScenes[newIdx]] = [newScenes[newIdx], newScenes[idx]];
    newScenes.forEach((s, i) => (s.order = i + 1));

    setTimeline({ ...timeline, scenes: newScenes });
  }, [timeline]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-12 text-center">
        <div className="animate-pulse text-[var(--fg-secondary)]">Đang tải timeline…</div>
      </div>
    );
  }

  const selectedSceneData = timeline?.scenes.find(s => s.id === selectedScene);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-up">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <a href={`/projects/${id}`} className="text-sm text-[var(--brand-400)] hover:underline">
            ← Back to Project
          </a>
          <span className="text-[var(--fg-tertiary)]">|</span>
          <span className="text-sm text-[var(--fg-tertiary)]">
            {project?.brief?.topic || `Project ${id}`}
          </span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          <span className="gradient-text">Timeline Debugger</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Visualize và edit <code className="text-[var(--brand-300)]">timelines.model</code> JSONB data.
        </p>
      </div>

      {/* Stats Bar */}
      <div className="glass rounded-xl p-4 flex items-center gap-6">
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Total Duration</span>
          <p className="text-xl font-bold">{timeline?.total_duration_seconds.toFixed(1)}s</p>
        </div>
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Scenes</span>
          <p className="text-xl font-bold">{timeline?.scenes.length}</p>
        </div>
        <div>
          <span className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Version</span>
          <p className="text-xl font-bold">{timeline?.version}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => setJsonMode(!jsonMode)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              jsonMode ? 'bg-[var(--brand-500)] text-white' : 'bg-[var(--surface)] border border-[var(--glass-border)]'
            }`}
          >
            {jsonMode ? 'Form View' : 'JSON View'}
          </button>
          <button
            onClick={addScene}
            className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 text-sm font-medium"
          >
            + Add Scene
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {saved && (
        <div className="p-3 rounded-lg bg-green-500/20 text-green-400 text-sm">
          ✓ Timeline saved successfully!
        </div>
      )}

      {/* Main Content */}
      {jsonMode ? (
        /* JSON Editor */
        <div className="glass rounded-2xl p-4">
          <textarea
            value={jsonText}
            onChange={(e) => handleJsonChange(e.target.value)}
            className="w-full h-[500px] bg-[var(--surface)] border border-[var(--glass-border)] rounded-lg p-4 font-mono text-sm resize-none"
            spellCheck={false}
          />
          <p className="text-xs text-[var(--fg-tertiary)] mt-2">
            ⚠️ Edit JSON directly. Ensure valid JSON before saving.
          </p>
        </div>
      ) : (
        /* Visual Timeline Editor */
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Scene List */}
          <div className="lg:col-span-2 glass rounded-2xl p-4">
            <h2 className="text-lg font-semibold mb-4">Scenes ({timeline?.scenes.length})</h2>
            
            {timeline?.scenes.length === 0 ? (
              <div className="text-center py-12 text-[var(--fg-tertiary)]">
                <p>No scenes yet.</p>
                <button onClick={addScene} className="mt-2 text-[var(--brand-400)] hover:underline">
                  Add your first scene
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {timeline?.scenes.map((scene, idx) => (
                  <div
                    key={scene.id}
                    onClick={() => setSelectedScene(scene.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedScene === scene.id
                        ? 'border-[var(--brand-500)] bg-[var(--brand-500)]/10'
                        : 'border-[var(--glass-border)] bg-[var(--surface)] hover:border-[var(--brand-500)]/50'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      {/* Reorder Buttons */}
                      <div className="flex flex-col gap-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); moveScene(scene.id, 'up'); }}
                          disabled={idx === 0}
                          className="text-xs px-1 text-[var(--fg-tertiary)] disabled:opacity-30"
                        >
                          ▲
                        </button>
                        <span className="text-xs font-mono text-[var(--fg-tertiary)]">
                          {scene.order}
                        </span>
                        <button
                          onClick={(e) => { e.stopPropagation(); moveScene(scene.id, 'down'); }}
                          disabled={idx === (timeline?.scenes.length ?? 0) - 1}
                          className="text-xs px-1 text-[var(--fg-tertiary)] disabled:opacity-30"
                        >
                          ▼
                        </button>
                      </div>

                      {/* Scene Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-[var(--brand-500)]/20 text-[var(--brand-300)] text-xs">
                            {scene.visual?.type || 'text'}
                          </span>
                          <span className="text-sm font-medium truncate">
                            {scene.voice_line?.text?.slice(0, 40) || 'No voice line'}
                          </span>
                        </div>
                        {scene.voice_line?.text && (
                          <p className="text-xs text-[var(--fg-tertiary)] truncate mt-1">
                            "{scene.voice_line.text.slice(0, 60)}..."
                          </p>
                        )}
                      </div>

                      {/* Duration */}
                      <div className="text-right">
                        <span className="text-sm font-mono">
                          {scene.duration_seconds.toFixed(1)}s
                        </span>
                      </div>

                      {/* Delete */}
                      <button
                        onClick={(e) => { e.stopPropagation(); deleteScene(scene.id); }}
                        className="text-red-400 hover:text-red-300 text-sm px-2"
                      >
                        ✕
                      </button>
                    </div>

                    {/* Timeline Bar */}
                    <div className="mt-3 h-2 rounded-full bg-[var(--surface)] overflow-hidden">
                      <div
                        className="h-full gradient-bg rounded-full"
                        style={{ width: `${(scene.duration_seconds / (timeline?.total_duration_seconds || 1)) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Timeline Visualization */}
            {timeline && timeline.scenes.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold mb-2">Timeline Bar</h3>
                <div className="h-8 rounded-lg bg-[var(--surface)] overflow-hidden flex">
                  {timeline.scenes.map((scene, idx) => (
                    <div
                      key={scene.id}
                      onClick={() => setSelectedScene(scene.id)}
                      title={`Scene ${scene.order}: ${scene.duration_seconds.toFixed(1)}s`}
                      className={`h-full border-r border-[var(--surface)] cursor-pointer hover:opacity-80 transition-opacity ${
                        selectedScene === scene.id ? 'gradient-bg' : 'bg-[var(--brand-500)]/30'
                      }`}
                      style={{ width: `${(scene.duration_seconds / timeline.total_duration_seconds) * 100}%` }}
                    />
                  ))}
                </div>
                <div className="flex justify-between mt-1 text-xs text-[var(--fg-tertiary)]">
                  <span>0s</span>
                  <span>{timeline.total_duration_seconds.toFixed(1)}s</span>
                </div>
              </div>
            )}
          </div>

          {/* Scene Editor Panel */}
          <div className="glass rounded-2xl p-4">
            <h2 className="text-lg font-semibold mb-4">
              {selectedSceneData ? `Edit Scene ${selectedSceneData.order}` : 'Select a Scene'}
            </h2>

            {selectedSceneData ? (
              <div className="space-y-4">
                <FormField label="Duration (seconds)">
                  <input
                    type="number"
                    value={selectedSceneData.duration_seconds}
                    onChange={(e) => updateScene(selectedSceneData.id, {
                      duration_seconds: Math.max(1, parseFloat(e.target.value) || 0)
                    })}
                    step={0.5}
                    min={0.5}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  />
                </FormField>

                <FormField label="Visual Type">
                  <select
                    value={selectedSceneData.visual?.type || 'text'}
                    onChange={(e) => updateScene(selectedSceneData.id, {
                      visual: { ...selectedSceneData.visual, type: e.target.value as any }
                    })}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  >
                    <option value="text">Text</option>
                    <option value="image">Image</option>
                    <option value="video">Video</option>
                    <option value="slideshow">Slideshow</option>
                  </select>
                </FormField>

                <FormField label="Visual Content">
                  <textarea
                    value={selectedSceneData.visual?.content || ''}
                    onChange={(e) => updateScene(selectedSceneData.id, {
                      visual: {
                        type: (selectedSceneData.visual?.type ?? 'text') as 'text' | 'image' | 'video' | 'slideshow',
                        content: e.target.value,
                        asset_url: selectedSceneData.visual?.asset_url,
                      }
                    })}
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] resize-none"
                    placeholder="Text content or asset URL..."
                  />
                </FormField>

                <FormField label="Transition">
                  <select
                    value={selectedSceneData.transition || 'cut'}
                    onChange={(e) => updateScene(selectedSceneData.id, { transition: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  >
                    <option value="cut">Cut</option>
                    <option value="fade">Fade</option>
                    <option value="dissolve">Dissolve</option>
                    <option value="wipe">Wipe</option>
                  </select>
                </FormField>

                <div className="pt-4 border-t border-[var(--glass-border)]">
                  <h3 className="text-sm font-semibold mb-3">Voice Line</h3>
                  
                  <FormField label="Text">
                    <textarea
                      value={selectedSceneData.voice_line?.text || ''}
                      onChange={(e) => updateScene(selectedSceneData.id, {
                        voice_line: { ...selectedSceneData.voice_line!, text: e.target.value }
                      })}
                      rows={4}
                      className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] resize-none"
                      placeholder="Voice line script..."
                    />
                  </FormField>

                  <div className="mt-2 flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      selectedSceneData.voice_line?.status === 'success' ? 'bg-green-500/20 text-green-400' :
                      selectedSceneData.voice_line?.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {selectedSceneData.voice_line?.status || 'pending'}
                    </span>
                    {selectedSceneData.voice_line?.audio_url && (
                      <a
                        href={selectedSceneData.voice_line.audio_url}
                        target="_blank"
                        rel="noopener"
                        className="text-xs text-[var(--brand-400)] hover:underline"
                      >
                        🔊 Play
                      </a>
                    )}
                  </div>
                </div>

                <div className="pt-4 border-t border-[var(--glass-border)]">
                  <p className="text-xs text-[var(--fg-tertiary)] font-mono">
                    ID: {selectedSceneData.id}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-[var(--fg-tertiary)]">
                <p>Click on a scene to edit</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">{label}</label>
      {children}
    </div>
  );
}
