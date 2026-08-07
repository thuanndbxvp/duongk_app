'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Section } from '@/components/section';
import { ColorPalette } from '@/components/color-palette';
import { TypographyList } from '@/components/typography-list';
import { CharacterRefs } from '@/components/character-refs';
import { BackgroundRefs } from '@/components/background-refs';

export default function StyleBibleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [bible, setBible] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/style-bibles/${id}`)
      .then(r => r.json())
      .then(setBible)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-4xl mx-auto py-12 animate-pulse text-[var(--fg-secondary)]">Loading...</div>;
  if (!bible) return <div className="max-w-4xl mx-auto py-12 text-red-400">Style Bible not found</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{bible.name}</h1>
          {bible.description && <p className="text-sm text-[var(--fg-secondary)] mt-1">{bible.description}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={async () => {
            await fetch(`/api/style-bibles/${id}/preview`, { method: 'POST' });
            alert('Preview generation started');
          }} className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium">
            🖼️ Preview
          </button>
        </div>
      </div>

      {/* Color Palette */}
      <Section title="🎨 Colors" onAdd={() => {}}>
        <ColorPalette
          colors={[]}
          onAdd={(hex, name) => { /* POST /api/style-bibles/{id}/sections */ }}
        />
      </Section>

      {/* Typography */}
      <Section title="🔤 Typography" onAdd={() => {}}>
        <TypographyList
          fonts={[]}
          onAdd={(font, weight, size) => { /* POST sections */ }}
        />
      </Section>

      {/* Characters */}
      <Section title="👤 Characters" onAdd={() => {}}>
        <CharacterRefs
          refs={[]}
          onAdd={(name) => { /* POST sections */ }}
        />
      </Section>

      {/* Backgrounds */}
      <Section title="🏞️ Backgrounds" onAdd={() => {}}>
        <BackgroundRefs
          refs={[]}
          onAdd={(name) => { /* POST sections */ }}
        />
      </Section>
    </div>
  );
}
