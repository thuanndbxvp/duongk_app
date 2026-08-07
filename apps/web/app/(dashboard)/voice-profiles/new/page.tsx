'use client';

import { VoiceForm } from '@/components/voice-form';

export default function NewVoicePage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">🎙️ Create Voice Profile</h1>
      <VoiceForm />
    </div>
  );
}
