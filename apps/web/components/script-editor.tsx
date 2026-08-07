'use client';

import { useState, useEffect } from 'react';
import { ScriptRegenerateDialog } from '@/components/script-regenerate-dialog';
import { ScriptVersionDropdown } from '@/components/script-version-dropdown';
import { ScriptDiffModal } from '@/components/script-diff-modal';

interface ScriptData {
  hook: string;
  body: string;
  cta: string;
}

interface Version {
  version: number;
  content: string;
  created_at: string;
}

interface Props {
  script: ScriptData;
  scriptId?: string;
  currentVersion?: number;
  onVersionChange?: (version: number) => void;
}

export function ScriptEditor({ script, scriptId, currentVersion = 1, onVersionChange }: Props) {
  const [showRegenerate, setShowRegenerate] = useState(false);
  const [versions, setVersions] = useState<Version[]>([]);

  useEffect(() => {
    if (!scriptId) return;
    fetch(`/api/scripts/${scriptId}/versions`)
      .then(r => r.json())
      .then(d => setVersions(d.versions || []))
      .catch(() => {});
  }, [scriptId]);

  return (
    <div className="space-y-6">
      {/* Header with regenerate + version */}
      {scriptId && (
        <div className="flex items-center justify-between">
          <ScriptVersionDropdown
            scriptId={scriptId}
            currentVersion={currentVersion}
            onVersionChange={onVersionChange || (() => {})}
          />
          <div className="flex gap-2">
            {versions.length >= 2 && (
              <ScriptDiffModal versions={versions} onSelect={onVersionChange} />
            )}
            <button
              onClick={() => setShowRegenerate(true)}
              className="px-3 py-1.5 rounded-lg gradient-bg text-white text-xs font-medium"
            >
              🔄 Regenerate
            </button>
          </div>
        </div>
      )}

      <ScriptRegenerateDialog
        scriptId={scriptId || ''}
        open={showRegenerate}
        onClose={() => setShowRegenerate(false)}
      />

      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">1</span> 
          Hook (30 giây)
        </h2>
        <textarea value={script.hook} readOnly
          className="w-full p-4 border rounded h-32 bg-gray-50 focus:outline-none" />
      </div>

      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">2</span> 
          Nội dung chính (Body)
        </h2>
        <textarea value={script.body} readOnly
          className="w-full p-4 border rounded h-96 bg-gray-50 focus:outline-none" />
      </div>

      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">3</span> 
          Kêu gọi hành động (CTA)
        </h2>
        <textarea value={script.cta} readOnly
          className="w-full p-4 border rounded h-24 bg-gray-50 focus:outline-none" />
      </div>
    </div>
  );
}

