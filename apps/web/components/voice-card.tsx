'use client';

import Link from 'next/link';

interface VoiceCardProps {
  id: string;
  name: string;
  provider: string;
  language: string;
  gender?: string;
  sample_url?: string;
}

export function VoiceCard({ id, name, provider, language, gender, sample_url }: VoiceCardProps) {
  return (
    <Link href={`/voice-profiles/${id}`}
      className="glass-strong rounded-xl p-4 space-y-3 hover:border-[var(--brand-400)]/30 transition block">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">{name}</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--fg-tertiary)]">{provider}</span>
      </div>
      <div className="flex gap-2 text-xs text-[var(--fg-secondary)]">
        <span>{language}</span>
        {gender && <span>· {gender}</span>}
      </div>
      {sample_url && (
        <audio controls src={sample_url} className="w-full h-8" preload="none" />
      )}
    </Link>
  );
}
