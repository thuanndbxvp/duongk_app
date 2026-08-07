'use client';

import { useState } from 'react';

export function AssetUpload({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleUpload() {
    if (!file) { setError('Select a file'); return; }
    if (file.size > 200 * 1024 * 1024) { setError('File too large (max 200MB)'); return; }
    setLoading(true); setError('');

    const fd = new FormData();
    fd.append('file', file);
    fd.append('name', file.name);

    try {
      const r = await fetch('/api/assets', { method: 'POST', body: fd });
      if (r.ok) { onUploaded(); setFile(null); }
      else { const d = await r.json(); setError(d.detail || 'Upload failed'); }
    } catch { setError('Cannot connect'); }
    setLoading(false);
  }

  return (
    <div className="glass-strong rounded-xl p-4 space-y-3">
      <label className="block w-full h-24 rounded-xl border-2 border-dashed border-[var(--glass-border)] flex flex-col items-center justify-center cursor-pointer hover:border-[var(--brand-400)]/50">
        <span className="text-2xl mb-1">📤</span>
        <span className="text-xs text-[var(--fg-secondary)]">{file ? file.name : 'Click to select file'}</span>
        <input type="file" className="hidden" accept="image/*,video/*,audio/*"
          onChange={e => setFile(e.target.files?.[0] || null)} />
      </label>
      {file && <button onClick={handleUpload} disabled={loading}
        className="w-full h-9 rounded-lg gradient-bg text-white text-xs font-medium disabled:opacity-50">
        {loading ? 'Uploading...' : 'Upload'}
      </button>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
