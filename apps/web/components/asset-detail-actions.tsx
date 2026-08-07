'use client';

import { useRouter } from 'next/navigation';

interface Props { asset: { id: string; name?: string }; }

export function AssetDetailActions({ asset }: Props) {
  const router = useRouter();

  const handleDelete = async () => {
    if (!confirm('Delete this asset?')) return;
    await fetch(`/api/assets/${asset.id}`, { method: 'DELETE' });
    router.push('/assets');
  };

  return (
    <div className="flex gap-2 mt-4">
      <button onClick={() => window.open(`/api/assets/${asset.id}/download`, '_blank')}
        className="px-3 py-1.5 rounded-lg gradient-bg text-white text-xs font-medium">📥 Download</button>
      <button onClick={handleDelete}
        className="px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-xs">Delete</button>
    </div>
  );
}
