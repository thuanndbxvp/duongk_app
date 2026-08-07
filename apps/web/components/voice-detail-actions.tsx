'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface Props {
  voice: { id: string; name: string; provider: string; language: string; gender?: string };
}

export function VoiceDetailActions({ voice }: Props) {
  const router = useRouter();
  const [testText, setTestText] = useState('Xin chào, đây là test voice.');
  const [testAudioUrl, setTestAudioUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleTest = async () => {
    setIsLoading(true);
    try {
      const r = await fetch(`/api/voices/${voice.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: testText }),
      });
      if (!r.ok) throw new Error(await r.text());
      const { audio_url } = await r.json();
      setTestAudioUrl(audio_url);
    } catch (e) {
      alert('Lỗi: ' + (e as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Xóa voice này?')) return;
    await fetch(`/api/voices/${voice.id}`, { method: 'DELETE' });
    router.push('/voice-profiles');
  };

  return (
    <div className="mt-6 space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Test voice</h3>
        <textarea value={testText} onChange={e => setTestText(e.target.value)} rows={3}
          className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
        <button onClick={handleTest} disabled={isLoading}
          className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
          {isLoading ? '⏳ Generating...' : '🔊 Test'}
        </button>
        {testAudioUrl && <audio controls src={testAudioUrl} className="w-full mt-2" />}
      </div>
      <div className="flex gap-2">
        <button onClick={() => router.push(`/voice-profiles/${voice.id}/edit`)}
          className="px-4 py-2 rounded-lg bg-white/[0.06] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)]">Edit</button>
        <button onClick={handleDelete}
          className="px-4 py-2 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-sm">Delete</button>
      </div>
    </div>
  );
}
