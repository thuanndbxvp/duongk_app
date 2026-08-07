'use client';

import Link from 'next/link';

interface Asset {
  id: string;
  name?: string;
  storage_key?: string;
  mime_type?: string;
  size_bytes?: number;
  source?: string;
  status?: string;
}

export function AssetGrid({ assets, onSelect }: { assets: Asset[]; onSelect?: (id: string) => void }) {
  if (!assets || assets.length === 0) {
    return <p className="text-[var(--fg-tertiary)] text-center py-12">No assets found.</p>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {assets.map(a => (
        <Link key={a.id} href={`/assets/${a.id}`}
          className="glass rounded-xl overflow-hidden hover:border-[var(--brand-400)]/50 transition cursor-pointer">
          <div className="aspect-square bg-white/[0.04] flex items-center justify-center text-3xl">
            {a.mime_type?.startsWith('video') ? '🎬' : a.mime_type?.startsWith('audio') ? '🎵' : '🖼️'}
          </div>
          <div className="p-2 space-y-0.5">
            <p className="text-xs font-medium truncate">{a.name || a.storage_key?.split('/').pop() || 'Asset'}</p>
            <p className="text-[10px] text-[var(--fg-tertiary)]">{a.mime_type} · {((a.size_bytes || 0) / 1024 / 1024).toFixed(1)}MB</p>
          </div>
        </Link>
      ))}
    </div>
  );
}
