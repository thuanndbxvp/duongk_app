'use client';

import Link from 'next/link';

interface Props {
  id: string;
  name: string;
  description: string;
  version: number;
}

export function StyleBibleCard({ id, name, description, version }: Props) {
  return (
    <Link href={`/style-bibles/${id}`}
      className="glass-strong rounded-xl p-4 space-y-2 hover:border-[var(--brand-400)]/30 transition block">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">{name}</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--fg-tertiary)]">v{version}</span>
      </div>
      {description && <p className="text-xs text-[var(--fg-secondary)] line-clamp-2">{description}</p>}
    </Link>
  );
}
