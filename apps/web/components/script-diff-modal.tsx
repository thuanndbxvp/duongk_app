'use client';

import { useState } from 'react';

interface Version {
  version: number;
  content: string;
  created_at: string;
}

interface Props {
  versions: Version[];
  onSelect?: (version: number) => void;
}

function computeDiff(oldText: string, newText: string): { type: 'same' | 'added' | 'removed'; text: string }[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  const result: { type: 'same' | 'added' | 'removed'; text: string }[] = [];

  // Simple line-by-line diff
  const maxLen = Math.max(oldLines.length, newLines.length);
  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i];
    const newLine = newLines[i];

    if (oldLine === undefined) {
      result.push({ type: 'added', text: newLine });
    } else if (newLine === undefined) {
      result.push({ type: 'removed', text: oldLine });
    } else if (oldLine === newLine) {
      result.push({ type: 'same', text: oldLine });
    } else {
      result.push({ type: 'removed', text: oldLine });
      result.push({ type: 'added', text: newLine });
    }
  }

  return result;
}

export function ScriptDiffModal({ versions, onSelect }: Props) {
  const [leftVer, setLeftVer] = useState(versions.length > 1 ? versions[1]?.version : null);
  const [rightVer, setRightVer] = useState(versions[0]?.version);
  const [show, setShow] = useState(false);

  if (versions.length < 2) {
    return (
      <p className="text-xs text-[var(--fg-tertiary)]">
        Need at least 2 versions to compare.
      </p>
    );
  }

  const left = versions.find(v => v.version === leftVer);
  const right = versions.find(v => v.version === rightVer);
  const diff = left && right ? computeDiff(left.content, right.content) : [];

  return (
    <>
      <button
        onClick={() => setShow(true)}
        className="px-3 py-1.5 rounded-lg bg-white/[0.06] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)] hover:bg-white/[0.1] transition"
      >
        📄 Compare versions
      </button>

      {show && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="glass-strong rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--glass-border)]">
              <h2 className="font-semibold">Compare Versions</h2>
              <button onClick={() => setShow(false)} className="text-[var(--fg-tertiary)] hover:text-white">✕</button>
            </div>

            {/* Version selectors */}
            <div className="flex gap-4 p-4 border-b border-[var(--glass-border)]">
              <div className="flex-1">
                <label className="text-xs text-[var(--fg-tertiary)] block mb-1">Older version</label>
                <select
                  value={leftVer || ''}
                  onChange={e => setLeftVer(Number(e.target.value))}
                  className="w-full h-9 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm"
                >
                  {versions.map(v => (
                    <option key={v.version} value={v.version}>
                      v{v.version} — {new Date(v.created_at).toLocaleDateString('vi-VN')}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-xs text-[var(--fg-tertiary)] block mb-1">Newer version</label>
                <select
                  value={rightVer || ''}
                  onChange={e => setRightVer(Number(e.target.value))}
                  className="w-full h-9 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm"
                >
                  {versions.map(v => (
                    <option key={v.version} value={v.version}>
                      v{v.version} — {new Date(v.created_at).toLocaleDateString('vi-VN')}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Diff view */}
            <div className="flex-1 overflow-auto p-4 font-mono text-sm">
              {diff.map((line, i) => (
                <div
                  key={i}
                  className={`px-2 py-0.5 ${
                    line.type === 'added'
                      ? 'bg-green-500/20 text-green-300'
                      : line.type === 'removed'
                      ? 'bg-red-500/20 text-red-300'
                      : 'text-[var(--fg-secondary)]'
                  }`}
                >
                  {line.type === 'added' && '+ '}
                  {line.type === 'removed' && '- '}
                  {line.type === 'same' && '  '}
                  {line.text || ' '}
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-2 p-4 border-t border-[var(--glass-border)]">
              <button
                onClick={() => setShow(false)}
                className="px-4 py-2 rounded-lg bg-white/[0.06] text-sm text-[var(--fg-secondary)]"
              >
                Close
              </button>
              {onSelect && rightVer && (
                <button
                  onClick={() => { onSelect(rightVer); setShow(false); }}
                  className="px-4 py-2 rounded-lg gradient-bg text-white text-sm"
                >
                  Use v{rightVer}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
