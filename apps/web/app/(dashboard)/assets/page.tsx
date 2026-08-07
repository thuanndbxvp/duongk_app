'use client';

import { useEffect, useState } from 'react';
import { AssetGrid } from '@/components/asset-grid';
import { AssetFilters } from '@/components/asset-filters';
import { AssetUpload } from '@/components/asset-upload';

export default function AssetsPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [type, setType] = useState('');
  const [tag, setTag] = useState('');
  const [sort, setSort] = useState('created_desc');
  const [showUpload, setShowUpload] = useState(false);

  const fetchAssets = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (type) params.set('type', type);
    if (tag) params.set('tag', tag);
    params.set('sort', sort);
    fetch(`/api/assets?${params}`)
      .then(r => r.json())
      .then(d => setAssets(d.data || d || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAssets(); }, [type, sort]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">🖼️ Asset Library</h1>
        <button onClick={() => setShowUpload(!showUpload)}
          className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium">
          {showUpload ? 'Close' : '+ Upload'}
        </button>
      </div>

      {showUpload && <AssetUpload onUploaded={() => { setShowUpload(false); fetchAssets(); }} />}

      <AssetFilters type={type} setType={setType} tag={tag} setTag={setTag} sort={sort} setSort={setSort} />

      {loading ? (
        <div className="grid grid-cols-4 gap-3">
          {[1,2,3,4,5,6,7,8].map(i => <div key={i} className="glass rounded-xl aspect-square animate-pulse" />)}
        </div>
      ) : (
        <AssetGrid assets={assets} />
      )}
    </div>
  );
}
