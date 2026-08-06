'use client';

import { useState } from 'react';

interface Props {
  bible?: { id: string; name: string; visual_palette: Record<string,string>; lens_preference: string; motion_style: string; negative_prompt: string };
  onSave?: (data: Record<string,unknown>) => void;
}

const MOTIONS = ['ken_burns_zoom_in','ken_burns_zoom_out','pan_left','pan_right','tilt_up','tilt_down','static','dolly_zoom','tracking'];
const LENSES = ['24mm','35mm','50mm','85mm','135mm','200mm'];

export function StyleBibleEditor({ bible, onSave }: Props) {
  const [tab, setTab] = useState<'visual'|'characters'|'backgrounds'|'negative'>('visual');
  const [name, setName] = useState(bible?.name || '');
  const [palette, setPalette] = useState<Record<string,string>>(bible?.visual_palette || { primary: '#FFFFFF', secondary: '#000000', accent: '#3B82F6' });
  const [lens, setLens] = useState(bible?.lens_preference || '50mm');
  const [motion, setMotion] = useState(bible?.motion_style || 'ken_burns_zoom_in');
  const [negative, setNegative] = useState(bible?.negative_prompt || '');

  function handleSave() {
    onSave?.({ name, visual_palette: palette, lens_preference: lens, motion_style: motion, negative_prompt: negative });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Style Bible Name"
          className="flex-1 h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm" />
        <button onClick={handleSave} className="px-4 h-10 rounded-lg gradient-bg text-white text-sm font-medium">Save</button>
      </div>

      <div className="flex gap-1 p-1 rounded-lg bg-white/[0.04]">
        {(['visual','characters','backgrounds','negative'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-1.5 text-xs rounded-md ${tab===t?'gradient-bg text-white':'text-[var(--fg-tertiary)]'}`}>
            {t==='visual'?'🎨 Visual':t==='characters'?'👤 Chars':t==='backgrounds'?'🏞️ BG':'🚫 Negative'}
          </button>
        ))}
      </div>

      {tab === 'visual' && (
        <div className="space-y-4">
          {Object.entries(palette).map(([k,v]) => (
            <div key={k} className="flex items-center gap-3">
              <input value={k} onChange={e => { const n={...palette}; delete n[k]; n[e.target.value]=v; setPalette(n); }}
                className="w-24 h-10 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs" />
              <input type="color" value={v} onChange={e => setPalette({...palette,[k]:e.target.value})}
                className="w-10 h-10 rounded cursor-pointer" />
              <input value={v} onChange={e => setPalette({...palette,[k]:e.target.value})}
                className="flex-1 h-10 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs font-mono" />
            </div>
          ))}
          <button onClick={() => setPalette({...palette,['color'+(Object.keys(palette).length+1)]:'#888888'})}
            className="text-xs text-[var(--brand-400)]">+ Add color</button>
          <div className="grid grid-cols-2 gap-3">
            <select value={lens} onChange={e => setLens(e.target.value)}
              className="h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm">
              {LENSES.map(l => <option key={l}>{l}</option>)}
            </select>
            <select value={motion} onChange={e => setMotion(e.target.value)}
              className="h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm">
              {MOTIONS.map(m => <option key={m}>{m}</option>)}
            </select>
          </div>
        </div>
      )}

      {tab === 'negative' && (
        <textarea value={negative} onChange={e => setNegative(e.target.value)} rows={5} placeholder="low quality, blurry, watermark..."
          className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm" />
      )}

      {(tab === 'characters' || tab === 'backgrounds') && (
        <p className="text-sm text-[var(--fg-tertiary)] text-center py-8">👤 Drag assets from library to add {tab}.</p>
      )}
    </div>
  );
}
