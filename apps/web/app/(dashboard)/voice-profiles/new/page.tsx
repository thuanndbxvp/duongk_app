'use client';

import Link from 'next/link';
import { VoiceForm } from '@/components/voice-form';

export default function NewVoiceProfilePage() {
  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6 animate-fade-up">
      <Link href="/voice-profiles"
        className="inline-flex items-center gap-1 text-sm text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)] transition">
        ← Back to Voices
      </Link>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold">🎙️ Create Voice Profile</h1>
        <p className="text-sm text-[var(--fg-secondary)]">
          Configure a voice for text-to-speech in your videos.
        </p>
      </div>

      <VoiceForm />
    </div>
  );
}
