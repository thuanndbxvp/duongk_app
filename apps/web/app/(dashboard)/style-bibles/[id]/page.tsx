'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Section } from '@/components/section';
import { ColorPalette } from '@/components/color-palette';
import { TypographyList } from '@/components/typography-list';
import { CharacterRefs } from '@/components/character-refs';
import { BackgroundRefs } from '@/components/background-refs';

interface Bible {
  id: string;
  name: string;
  description?: string;
  visual_palette?: Record<string, string>;
  version?: number;
}

export default function StyleBibleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [bible, setBible] = useState<Bible | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`/api/style-bibles/${id}`)
      .then(r => r.json())
      .then(setBible)
      .finally(() => setLoading(false));
  }, [id]);

  async function patchBible(update: Partial<Bible>) {
    setSaving(true);
    try {
      const r = await fetch(`/api/style-bibles/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });
      if (r.ok) {
        const updated = await r.json();
        setBible(prev => prev ? { ...prev, ...updated } : updated);
      }
    } finally {
      setSaving(false);
    }
  }

  async function addColor(hex: string, name: string) {
    const colors = bible?.visual_palette || {};
    colors[name] = hex;
    await patchBible({ visual_palette: colors });
  }

  async function addAssetRef(refType: 'character' | 'background', name: string) {
    // TODO: Open asset picker modal → call /api/style-bibles/{id}/assets
    alert(`Asset picker for ${refType} — coming soon`);
  }

  async function addFont(font: string, weight: string, size: string) {
    // TODO: Backend needs typography field in schema
    alert('Typography editing — coming soon');
  }

  if (loading) return <div className="max-w-4xl mx-auto py-12 animate-pulse text-[var(--fg-secondary)]">Loading...</div>;
  if (!bible) return <div className="max-w-4xl mx-auto py-12 text-red-400">Style Bible not found</div>;

  const colors = bible.visual_palette || {};
  const colorList = Object.entries(colors).map(([name, hex], i) => ({ id: String(i), hex, name }));

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{bible.name}</h1>
          {bible.description && <p className="text-sm text-[var(--fg-secondary)] mt-1">{bible.description}</p>}
          {bible.version && <p className="text-xs text-[var(--fg-tertiary)] mt-1">v{bible.version}</p>}
        </div>
        <div className="flex gap-2">
          {saving && <span className="text-xs text-[var(--brand-300)] animate-pulse">Saving...</span>}
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
        <ColorPalette colors={colorList} onAdd={addColor} />
      </Section>

      {/* Typography */}
      <Section title="🔤 Typography" onAdd={() => addFont('', '', '')}>
        <TypographyList fonts={[]} onAdd={addFont} />
      </Section>

      {/* Characters */}
      <Section title="👤 Characters" onAdd={() => addAssetRef('character', '')}>
        <CharacterRefs refs={[]} onAdd={(name) => addAssetRef('character', name)} />
      </Section>

      {/* Backgrounds */}
      <Section title="🏞️ Backgrounds" onAdd={() => addAssetRef('background', '')}>
        <BackgroundRefs refs={[]} onAdd={(name) => addAssetRef('background', name)} />
      </Section>
    </div>
  );
}
