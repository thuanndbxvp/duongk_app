'use client';

import { useState } from 'react';
import { regenerateScript } from '@/lib/analysis-client';

interface Props {
  scriptId: string;
  open: boolean;
  onClose: () => void;
}

export function ScriptRegenerateDialog({ scriptId, open, onClose }: Props) {
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!open) return null;

  const handleSubmit = async () => {
    if (!feedback.trim()) { setError('Vui lòng nhập feedback'); return; }
    setIsLoading(true);
    setError('');

    const result = await regenerateScript(scriptId, feedback);
    if (result.success) {
      window.location.reload();
    } else {
      setError(result.error || 'Regenerate failed');
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative glass-strong rounded-2xl p-6 w-full max-w-lg space-y-4 animate-scale-in">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">🔄 Regenerate Script</h3>
          <button onClick={onClose} className="text-[var(--fg-tertiary)] hover:text-white">✕</button>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--fg-secondary)]">Bạn muốn thay đổi gì?</label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="VD: 'Thêm chi tiết về nhân vật chính, giảm độ dài phần kết'"
            rows={4}
            className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)] resize-y"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading}
            className="px-4 py-2 rounded-lg border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)] disabled:opacity-50">
            Hủy
          </button>
          <button onClick={handleSubmit} disabled={isLoading}
            className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
            {isLoading ? '⏳ Đang generate...' : '🔄 Regenerate'}
          </button>
        </div>
      </div>
    </div>
  );
}
