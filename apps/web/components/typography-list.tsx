'use client';

interface Font { id: string; font: string; weight: string; size: string }

interface Props {
  fonts: Font[];
  onAdd: (font: string, weight: string, size: string) => void;
}

const FONTS = ['Inter', 'Roboto', 'Playfair Display', 'Montserrat', 'Merriweather', 'system-ui'];
const WEIGHTS = ['300', '400', '500', '600', '700', '900'];
const SIZES = ['12px', '14px', '16px', '18px', '24px', '32px', '48px'];

export function TypographyList({ fonts, onAdd }: Props) {
  const handleAdd = () => {
    const font = (document.getElementById('font-family') as HTMLSelectElement)?.value || 'Inter';
    const weight = (document.getElementById('font-weight') as HTMLSelectElement)?.value || '400';
    const size = (document.getElementById('font-size') as HTMLSelectElement)?.value || '16px';
    onAdd(font, weight, size);
  };

  return (
    <div className="space-y-3">
      {fonts.map(f => (
        <div key={f.id} className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.04]">
          <span className="text-sm text-[var(--fg-secondary)]">{f.font}</span>
          <span className="text-[10px] text-[var(--fg-tertiary)]">{f.weight} · {f.size}</span>
        </div>
      ))}
      <div className="flex gap-2">
        <select id="font-family" className="h-9 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs">
          {FONTS.map(f => <option key={f}>{f}</option>)}
        </select>
        <select id="font-weight" className="h-9 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs">
          {WEIGHTS.map(w => <option key={w}>{w}</option>)}
        </select>
        <select id="font-size" className="h-9 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs">
          {SIZES.map(s => <option key={s}>{s}</option>)}
        </select>
        <button onClick={handleAdd} className="px-3 h-9 rounded-lg gradient-bg text-white text-xs font-medium">Add</button>
      </div>
    </div>
  );
}
