'use client';

import { useState } from 'react';

interface Clip {
  scene_id: string;
  scene_index: number;
  asset_id: string | null;
  start: number;
  duration: number;
  fit_mode: string;
  motion: string;
  transition_in?: string;
  transition_out?: string;
}

interface AudioTrack {
  kind: string;
  track_id: string | null;
  start: number;
  duration: number;
}

interface TimelineModel {
  schema_version: number;
  total_duration: number;
  clips: Clip[];
  transitions?: { from_clip: number; to_clip: number; type: string; duration: number }[];
  audio_tracks: AudioTrack[];
  subtitle_track?: { source: string; style: string; safe_area: string };
  output?: { width: number; height: number; fps: number; codec: string };
}

interface Props {
  timeline: TimelineModel | null;
  loading?: boolean;
}

function fmt(sec: number) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function TimelineEditor({ timeline, loading }: Props) {
  const [selectedClip, setSelectedClip] = useState<number | null>(null);

  if (loading) {
    return <div className="p-8 text-center text-[var(--fg-secondary)] animate-pulse">Đang tải timeline…</div>;
  }

  if (!timeline || !timeline.clips || timeline.clips.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--fg-tertiary)]">Chưa có timeline. Hãy chạy TTS voice trước.</p>
      </div>
    );
  }

  const totalWidth = 800;
  const scale = totalWidth / timeline.total_duration;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="flex items-center gap-4 text-sm">
        <span className="px-2 py-0.5 rounded bg-green-500/10 text-green-400 text-xs">
          v{timeline.schema_version}
        </span>
        <span className="text-[var(--fg-secondary)]">
          {timeline.clips.length} clips · {fmt(timeline.total_duration)}
        </span>
        {timeline.output && (
          <span className="text-[var(--fg-tertiary)] text-xs">
            {timeline.output.width}×{timeline.output.height} @{timeline.output.fps}fps
          </span>
        )}
      </div>

      {/* Timeline track */}
      <div className="glass-strong rounded-xl p-4 overflow-x-auto">
        <div className="relative" style={{ width: totalWidth, minHeight: 80 }}>
          {/* Time ruler */}
          <div className="flex h-5 mb-2 relative">
            {Array.from({ length: Math.ceil(timeline.total_duration / 30) + 1 }).map((_, i) => (
              <div key={i} className="absolute text-[10px] text-[var(--fg-tertiary)]" style={{ left: i * 30 * scale }}>
                {fmt(i * 30)}
              </div>
            ))}
          </div>

          {/* Clip bars */}
          <div className="relative h-12">
            {timeline.clips.map((clip, i) => {
              const left = clip.start * scale;
              const width = Math.max(clip.duration * scale, 8);
              return (
                <div
                  key={i}
                  onClick={() => setSelectedClip(i)}
                  className={`absolute h-10 rounded-lg cursor-pointer transition-all flex items-center px-2 overflow-hidden ${
                    selectedClip === i
                      ? 'gradient-bg text-white ring-2 ring-white/30'
                      : 'bg-white/[0.08] text-[var(--fg-secondary)] hover:bg-white/[0.12]'
                  }`}
                  style={{ left, width }}
                  title={`Scene ${clip.scene_index}: ${fmt(clip.duration)}`}
                >
                  <span className="text-[10px] font-mono truncate">#{clip.scene_index}</span>
                </div>
              );
            })}
          </div>

          {/* Audio tracks indicator */}
          <div className="mt-3 flex gap-2">
            {timeline.audio_tracks.map((t, i) => (
              <div key={i} className={`text-[10px] px-2 py-0.5 rounded ${
                t.track_id ? 'bg-blue-500/10 text-blue-400' : 'bg-gray-500/10 text-[var(--fg-tertiary)]'
              }`}>
                🎵 {t.kind} {t.track_id ? '✓' : '(none)'}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Clip detail */}
      {selectedClip !== null && timeline.clips[selectedClip] && (
        <div className="glass-strong rounded-xl p-4 space-y-2">
          <h4 className="text-sm font-semibold">Clip #{timeline.clips[selectedClip].scene_index}</h4>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <span className="text-[var(--fg-tertiary)]">Start</span>
              <p className="font-mono">{fmt(timeline.clips[selectedClip].start)}</p>
            </div>
            <div>
              <span className="text-[var(--fg-tertiary)]">Duration</span>
              <p className="font-mono">{fmt(timeline.clips[selectedClip].duration)}</p>
            </div>
            <div>
              <span className="text-[var(--fg-tertiary)]">Motion</span>
              <p>{timeline.clips[selectedClip].motion}</p>
            </div>
            <div>
              <span className="text-[var(--fg-tertiary)]">Fit</span>
              <p>{timeline.clips[selectedClip].fit_mode}</p>
            </div>
            <div>
              <span className="text-[var(--fg-tertiary)]">Trans In</span>
              <p>{timeline.clips[selectedClip].transition_in || '-'}</p>
            </div>
            <div>
              <span className="text-[var(--fg-tertiary)]">Asset</span>
              <p className={timeline.clips[selectedClip].asset_id ? 'text-green-400' : 'text-red-400'}>
                {timeline.clips[selectedClip].asset_id ? '✓ Assigned' : '✗ Missing'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
