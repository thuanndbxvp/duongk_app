'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { VoiceCard } from '@/components/voice-card';

interface Voice {
  id: string;
  name: string;
  provider: string;
  language: string;
  gender?: string;
  sample_url?: string;
}

export default function VoiceProfilesPage() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/voices')
      .then(r => r.json())
      .then(d => setVoices(d.voices || d || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">🎙️ Voice Profiles</h1>
        <Link href="/voice-profiles/new"
          className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium">
          + New Voice
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="glass-strong rounded-xl p-6 animate-pulse h-32" />)}
        </div>
      ) : voices.length === 0 ? (
        <div className="text-center py-16 space-y-4">
          <p className="text-[var(--fg-tertiary)]">Bạn chưa có voice nào.</p>
          <Link href="/voice-profiles/new"
            className="inline-block px-6 py-3 rounded-lg gradient-bg text-white text-sm font-medium">
            🎙️ Tạo voice đầu tiên
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {voices.map(v => <VoiceCard key={v.id} {...v} />)}
        </div>
      )}
    </div>
  );
}
