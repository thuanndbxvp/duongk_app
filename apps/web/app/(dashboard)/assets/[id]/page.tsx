'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { AssetDetailActions } from '@/components/asset-detail-actions';

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [asset, setAsset] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/assets/${id}`)
      .then(r => r.json())
      .then(setAsset)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-2xl mx-auto py-12 animate-pulse text-[var(--fg-secondary)]">Loading...</div>;
  if (!asset) return <div className="max-w-2xl mx-auto py-12 text-red-400">Asset not found</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">{asset.name || asset.storage_key?.split('/').pop() || 'Asset'}</h1>

      <div className="glass-strong rounded-2xl p-6 space-y-4">
        <div className="aspect-video bg-white/[0.04] rounded-xl flex items-center justify-center text-6xl">
          {asset.mime_type?.startsWith('video') ? '🎬' : asset.mime_type?.startsWith('audio') ? '🎵' : '🖼️'}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-[var(--fg-tertiary)]">MIME</span><p className="font-medium">{asset.mime_type}</p></div>
          <div><span className="text-[var(--fg-tertiary)]">Size</span><p className="font-medium">{((asset.size_bytes || 0) / 1024 / 1024).toFixed(1)} MB</p></div>
          <div><span className="text-[var(--fg-tertiary)]">Source</span><p className="font-medium">{asset.source || 'upload'}</p></div>
          <div><span className="text-[var(--fg-tertiary)]">Status</span><p className="font-medium">{asset.status || 'ready'}</p></div>
          {asset.checksum && <div className="col-span-2"><span className="text-[var(--fg-tertiary)]">Checksum</span><p className="text-xs font-mono text-[var(--fg-secondary)] break-all">{asset.checksum}</p></div>}
        </div>

        <AssetDetailActions asset={asset} />
      </div>
    </div>
  );
}
