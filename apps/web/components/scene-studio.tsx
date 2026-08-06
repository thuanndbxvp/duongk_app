'use client';

import { useState } from 'react';

interface SceneData {
  id: string;
  scene_id: string;
  scene_index: number;
  narration: string;
  visual_description: string;
  image_prompt: string;
  estimated_duration: number;
  status: string;
  characters?: string[];
}

interface Props {
  scenes: SceneData[];
  onUpdate?: (sceneId: string, field: string, value: unknown) => void;
  onOpenDrawer?: (sceneId: string) => void;
  readOnly?: boolean;
}

export function SceneStudio({ scenes, onUpdate, onOpenDrawer, readOnly = false }: Props) {
  if (!scenes || scenes.length === 0) {
    return <p className="text-gray-500 italic p-4">Chưa có phân cảnh nào.</p>;
  }

  return (
    <div className="space-y-4">
      {scenes
        .sort((a, b) => a.scene_index - b.scene_index)
        .map((scene) => (
          <div
            key={scene.scene_id}
            className="glass-strong rounded-xl p-5 space-y-3 hover:border-[var(--brand-400)]/30 transition-colors"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg gradient-bg text-white text-sm font-bold flex items-center justify-center">
                  {scene.scene_index}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  scene.status === 'ready' ? 'bg-green-500/20 text-green-400' :
                  scene.status === 'rendered' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {scene.status}
                </span>
              </div>
              <span className="text-xs text-[var(--fg-tertiary)]">
                ~{scene.estimated_duration}s
              </span>
            </div>

            {/* Narration */}
            <div>
              <label className="text-xs font-medium text-[var(--fg-tertiary)] uppercase tracking-wide">
                Narration
              </label>
              {readOnly ? (
                <p className="text-sm text-[var(--fg-secondary)] mt-1">{scene.narration}</p>
              ) : (
                <textarea
                  value={scene.narration}
                  onChange={(e) => onUpdate?.(scene.scene_id, 'narration', e.target.value)}
                  rows={3}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)] resize-y"
                />
              )}
            </div>

            {/* Visual Desc */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-[var(--fg-tertiary)] uppercase tracking-wide">
                  Visual Description
                </label>
                {readOnly ? (
                  <p className="text-sm text-[var(--fg-secondary)] mt-1 line-clamp-2">{scene.visual_description}</p>
                ) : (
                  <input
                    type="text"
                    value={scene.visual_description}
                    onChange={(e) => onUpdate?.(scene.scene_id, 'visual_description', e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
                  />
                )}
              </div>
              <div>
                <label className="text-xs font-medium text-[var(--fg-tertiary)] uppercase tracking-wide">
                  Image Prompt
                </label>
                {readOnly ? (
                  <p className="text-sm text-[var(--fg-secondary)] mt-1 line-clamp-2">{scene.image_prompt}</p>
                ) : (
                  <input
                    type="text"
                    value={scene.image_prompt}
                    onChange={(e) => onUpdate?.(scene.scene_id, 'image_prompt', e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
                  />
                )}
              </div>
            </div>

            {/* Asset slot + actions */}
            <div className="flex items-center justify-between pt-2 border-t border-[var(--glass-border)]">
              <button
                type="button"
                onClick={() => onOpenDrawer?.(scene.scene_id)}
                className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.06] border border-[var(--glass-border)] text-[var(--fg-secondary)] hover:text-white hover:border-[var(--brand-400)]/50 transition"
              >
                🖼️ Chọn Asset
              </button>
              <span className="text-xs text-[var(--fg-tertiary)]">
                {scene.characters && scene.characters.length > 0
                  ? `👤 ${scene.characters.join(', ')}`
                  : ''}
              </span>
            </div>
          </div>
        ))}
    </div>
  );
}
