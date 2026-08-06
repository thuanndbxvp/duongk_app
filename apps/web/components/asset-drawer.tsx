'use client';

import { useState, useEffect } from 'react';

interface SearchResult {
  provider: string;
  provider_id: string;
  thumbnail_url: string;
  description: string;
  width?: number;
  height?: number;
  photographer?: string;
  pexels_url?: string;
}

interface AssetDrawerProps {
  open: boolean;
  sceneId: string | null;
  onClose: () => void;
  onAssign: (asset: SearchResult) => void;
}

type Tab = 'upload' | 'search' | 'library';

export function AssetDrawer({ open, sceneId, onClose, onAssign }: AssetDrawerProps) {
  const [tab, setTab] = useState<Tab>('search');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    if (!open) {
      setResults([]);
      setError('');
      setQuery('');
    }
  }, [open]);

  async function handleSearch() {
    if (!query.trim()) { setError('Vui lòng nhập từ khoá'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/assets/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'pexels', query, media_type: 'image' }),
      });
      const data = await res.json();
      if (res.ok) setResults(data.results || []);
      else setError(data.detail || 'Search failed');
    } catch { setError('Không thể kết nối'); }
    setLoading(false);
  }

  async function handleUpload() {
    if (!uploadFile) return;
    setLoading(true);
    try {
      const buffer = await uploadFile.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const checksum = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      const initRes = await fetch('/api/assets/upload-init', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: uploadFile.name, mime_type: uploadFile.type, size_bytes: uploadFile.size, checksum }),
      });
      const initData = await initRes.json();
      if (!initRes.ok) { setError(initData.detail || 'Upload init failed'); setLoading(false); return; }
      await fetch(initData.upload_url, { method: 'PUT', body: uploadFile, headers: { 'Content-Type': uploadFile.type } });
      await fetch('/api/assets/upload-complete', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: initData.asset_id, checksum }),
      });
      setUploadFile(null);
      setTab('library');
    } catch { setError('Upload thất bại'); }
    setLoading(false);
  }

  function handleAssign(result: SearchResult) {
    onAssign(result);
    onClose();
  }

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-md h-full glass-strong border-l border-[var(--glass-border)] overflow-y-auto animate-slide-left">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Asset Library</h3>
            <button onClick={onClose} className="text-[var(--fg-tertiary)] hover:text-white text-xl">✕</button>
          </div>
          {sceneId && <p className="text-xs text-[var(--fg-tertiary)]">Gán cho scene: {sceneId}</p>}

          {/* Tabs */}
          <div className="flex gap-1 p-1 rounded-lg bg-white/[0.04]">
            {(['search', 'upload', 'library'] as Tab[]).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`flex-1 py-2 text-xs font-medium rounded-md transition ${tab === t ? 'gradient-bg text-white' : 'text-[var(--fg-tertiary)] hover:text-white'}`}>
                {t === 'search' ? '🔍 Search' : t === 'upload' ? '📤 Upload' : '📁 Library'}
              </button>
            ))}
          </div>

          {/* Search Tab */}
          {tab === 'search' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <input type="text" value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Tìm kiếm Pexels..."
                  className="flex-1 h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
                />
                <button onClick={handleSearch} disabled={loading}
                  className="px-4 h-10 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
                  {loading ? '...' : 'Tìm'}
                </button>
              </div>
              {error && <p className="text-xs text-red-400">{error}</p>}
              <div className="grid grid-cols-2 gap-3">
                {results.map((r) => (
                  <div key={r.provider_id}
                    className="glass rounded-xl overflow-hidden hover:border-[var(--brand-400)]/50 transition cursor-pointer"
                    onClick={() => handleAssign(r)}>
                    {r.thumbnail_url ? (
                      <img src={r.thumbnail_url} alt={r.description} className="w-full h-32 object-cover" />
                    ) : (
                      <div className="w-full h-32 bg-white/[0.04] flex items-center justify-center text-2xl">🖼️</div>
                    )}
                    <div className="p-2">
                      <p className="text-xs text-[var(--fg-secondary)] line-clamp-1">{r.description}</p>
                      {r.photographer && <p className="text-xs text-[var(--fg-tertiary)] mt-0.5">📷 {r.photographer}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Tab */}
          {tab === 'upload' && (
            <div className="space-y-4">
              <label className="block w-full h-32 rounded-xl border-2 border-dashed border-[var(--glass-border)] flex flex-col items-center justify-center cursor-pointer hover:border-[var(--brand-400)]/50 transition">
                <span className="text-3xl mb-2">📤</span>
                <span className="text-sm text-[var(--fg-secondary)]">
                  {uploadFile ? uploadFile.name : 'Kéo thả hoặc click để chọn file'}
                </span>
                <input type="file" className="hidden" accept="image/*,video/*,audio/*"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
              </label>
              {uploadFile && (
                <button onClick={handleUpload} disabled={loading}
                  className="w-full h-10 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
                  {loading ? 'Đang upload...' : 'Upload'}
                </button>
              )}
              {error && <p className="text-xs text-red-400">{error}</p>}
            </div>
          )}

          {/* Library Tab */}
          {tab === 'library' && (
            <div className="text-center py-8 text-[var(--fg-tertiary)] text-sm">
              📁 Tính năng đang phát triển...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

