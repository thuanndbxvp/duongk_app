'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { StyleBibleCard } from '@/components/style-bible-card';

interface Bible {
  id: string;
  name: string;
  description: string;
  version: number;
}

export default function StyleBiblesPage() {
  const [bibles, setBibles] = useState<Bible[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/style-bibles')
      .then(r => r.json())
      .then(data => setBibles(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, []);

  const filtered = search ? bibles.filter(b => b.name.toLowerCase().includes(search.toLowerCase())) : bibles;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">🎨 Style Bibles</h1>
        <Link href="/style-bibles/new" className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium">
          + New Style Bible
        </Link>
      </div>

      <input type="search" value={search} onChange={e => setSearch(e.target.value)}
        placeholder="Search by name..."
        className="w-full h-10 px-4 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />

      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="glass-strong rounded-xl p-6 animate-pulse h-24" />)}
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-center text-[var(--fg-tertiary)] py-16">
          {search ? 'Không tìm thấy style bible nào.' : 'Chưa có style bible nào. Tạo style bible đầu tiên!'}
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {filtered.map(b => <StyleBibleCard key={b.id} {...b} />)}
        </div>
      )}
    </div>
  );
}
