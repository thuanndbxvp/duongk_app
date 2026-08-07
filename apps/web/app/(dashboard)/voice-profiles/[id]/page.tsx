'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { VoiceDetailActions } from '@/components/voice-detail-actions';

interface Voice {
  id: string;
  name: string;
  provider: string;
  language: string;
  gender?: string;
  sample_url?: string;
}

export default function VoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [voice, setVoice] = useState<Voice | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/voices/${id}`)
      .then(r => r.json())
      .then(setVoice)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-2xl mx-auto py-12 animate-pulse text-[var(--fg-secondary)]">Loading...</div>;
  if (!voice) return <div className="max-w-2xl mx-auto py-12 text-red-400">Voice not found</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">{voice.name}</h1>
      <div className="glass-strong rounded-2xl p-6 space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-[var(--fg-tertiary)]">Provider</span><p className="font-medium">{voice.provider}</p></div>
          <div><span className="text-[var(--fg-tertiary)]">Language</span><p className="font-medium">{voice.language}</p></div>
          {voice.gender && <div><span className="text-[var(--fg-tertiary)]">Gender</span><p className="font-medium">{voice.gender}</p></div>}
        </div>
        {voice.sample_url && <audio controls src={voice.sample_url} className="w-full" />}
        <VoiceDetailActions voice={voice} />
      </div>
    </div>
  );
}
