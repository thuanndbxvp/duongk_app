'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { VoiceDetailActions } from '@/components/voice-detail-actions';

interface Voice {
  id: string;
  name: string;
  provider: string;
  language: string;
  gender?: string;
  sample_url?: string;
  created_at?: string;
  updated_at?: string;
}

export default function VoiceProfileDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [voice, setVoice] = useState<Voice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/voices/${id}`)
      .then(r => {
        if (!r.ok) throw new Error('Not found');
        return r.json();
      })
      .then(d => setVoice(d))
      .catch(() => setError('Voice not found'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-white/10 rounded w-1/3" />
          <div className="h-4 bg-white/10 rounded w-1/4" />
          <div className="h-32 bg-white/10 rounded mt-6" />
        </div>
      </div>
    );
  }

  if (error || !voice) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center">
        <p className="text-red-400">{error || 'Voice not found'}</p>
        <Link href="/voice-profiles" className="mt-4 text-sm text-[var(--brand-300)] hover:underline">
          ← Back to Voices
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6 animate-fade-up">
      <Link href="/voice-profiles"
        className="inline-flex items-center gap-1 text-sm text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)] transition">
        ← Back to Voices
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{voice.name}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-[var(--fg-secondary)]">
            <span className="px-2 py-0.5 rounded glass text-xs">{voice.provider}</span>
            <span>{voice.language}</span>
            {voice.gender && <span>{voice.gender === 'male' ? '👨' : '👩'}</span>}
          </div>
        </div>
        <VoiceDetailActions voice={voice} />
      </div>

      {/* Metadata */}
      <div className="glass rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-semibold text-[var(--fg-secondary)]">Details</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-[var(--fg-tertiary)] text-xs">ID</p>
            <code className="text-xs text-[var(--fg-secondary)]">{voice.id}</code>
          </div>
          {voice.created_at && (
            <div>
              <p className="text-[var(--fg-tertiary)] text-xs">Created</p>
              <p className="text-[var(--fg-secondary)]">{new Date(voice.created_at).toLocaleDateString('vi-VN')}</p>
            </div>
          )}
          {voice.updated_at && (
            <div>
              <p className="text-[var(--fg-tertiary)] text-xs">Updated</p>
              <p className="text-[var(--fg-secondary)]">{new Date(voice.updated_at).toLocaleDateString('vi-VN')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Sample Audio */}
      {voice.sample_url && (
        <div className="glass rounded-xl p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[var(--fg-secondary)]">Sample Audio</h2>
          <audio controls src={voice.sample_url} className="w-full" />
        </div>
      )}
    </div>
  );
}
