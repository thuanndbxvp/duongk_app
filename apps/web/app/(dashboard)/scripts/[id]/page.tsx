'use client';

import { useEffect, useState } from 'react';
import { SceneTimeline } from '@/components/scene-timeline';

interface Script {
  id: string;
  topic: string;
  script: { title: string; hook: string; body: string; cta: string };
  scenes: any[];
}

export default function ScriptEditorPage({ params }: { params: { id: string } }) {
  const [script, setScript] = useState<Script | null>(null);

  useEffect(() => {
    fetch(`/api/scripts/${params.id}`)
      .then((r) => r.json())
      .then(setScript);
  }, [params.id]);

  if (!script) return <div className="min-h-screen flex items-center justify-center text-[var(--fg-secondary)]">Loading…</div>;

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">{script.script.title}</h1>
      <p className="text-[var(--fg-tertiary)] mb-6">Chủ đề: {script.topic}</p>

      <div className="grid lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Hook (30 giây)</h2>
          <textarea
            value={script.script.hook}
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-32"
          />

          <h2 className="text-xl font-semibold mt-4 mb-2">Body</h2>
          <textarea
            value={script.script.body}
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-96"
          />

          <h2 className="text-xl font-semibold mt-4 mb-2">CTA</h2>
          <textarea
            value={script.script.cta}
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-24"
          />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">Scenes</h2>
          <SceneTimeline scenes={script.scenes} />
        </div>
      </div>
    </main>
  );
}
