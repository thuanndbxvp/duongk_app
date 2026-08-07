'use client';

import Link from 'next/link';

export function ChannelList({ channels }: { channels: { id: string; name: string; url: string; created_at: string }[] }) {
  if (!channels || channels.length === 0) return <p className="text-xs text-[var(--fg-tertiary)]">No channels tracked.</p>;
  return (
    <div className="space-y-2">
      {channels.map(c => (
        <Link key={c.id} href={`/channel-collector/${c.id}`}
          className="block glass rounded-lg p-3 hover:border-[var(--brand-400)]/30 transition">
          <p className="text-sm font-medium">{c.name}</p>
          <p className="text-[10px] text-[var(--fg-tertiary)] truncate">{c.url}</p>
        </Link>
      ))}
    </div>
  );
}
