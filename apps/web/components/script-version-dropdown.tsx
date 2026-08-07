'use client';

import { useState, useEffect } from 'react';
import { fetchScriptVersions } from '@/lib/analysis-client';

interface Props {
  scriptId: string;
  currentVersion: number;
  onVersionChange: (version: number) => void;
  onCompare?: (v1: number, v2: number) => void;
}

export function ScriptVersionDropdown({ scriptId, currentVersion, onVersionChange, onCompare }: Props) {
  const [versions, setVersions] = useState<{ version: number; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScriptVersions(scriptId)
      .then(setVersions)
      .finally(() => setLoading(false));
  }, [scriptId]);

  if (loading) return <span className="text-xs text-[var(--fg-tertiary)]">Loading versions...</span>;
  if (versions.length <= 1) return <span className="text-xs text-[var(--fg-tertiary)]">v{currentVersion} (only)</span>;

  return (
    <div className="flex items-center gap-2">
      <select
        value={currentVersion}
        onChange={(e) => onVersionChange(Number(e.target.value))}
        className="h-8 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs focus:outline-none focus:border-[var(--brand-400)]"
      >
        {versions.map((v) => (
          <option key={v.version} value={v.version}>
            v{v.version} — {new Date(v.created_at).toLocaleDateString('vi-VN')}
          </option>
        ))}
      </select>
      {onCompare && currentVersion !== versions[0]?.version && (
        <button
          onClick={() => onCompare(versions[0].version, currentVersion)}
          className="text-xs px-2 py-1 rounded bg-white/[0.06] border border-[var(--glass-border)] text-[var(--fg-secondary)] hover:text-white"
        >
          Compare with latest
        </button>
      )}
    </div>
  );
}
