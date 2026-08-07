'use client';

interface Color { id: string; hex: string; name: string }

interface Props {
  colors: Color[];
  onAdd: (hex: string, name: string) => void;
}

export function ColorPalette({ colors, onAdd }: Props) {
  const handleAdd = () => {
    const hex = (document.getElementById('color-hex') as HTMLInputElement)?.value || '#3b82f6';
    const name = (document.getElementById('color-name') as HTMLInputElement)?.value || '';
    if (name) { onAdd(hex, name); }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        {colors.map(c => (
          <div key={c.id} className="text-center">
            <div style={{ background: c.hex }} className="w-14 h-14 rounded-lg shadow-lg border border-white/10" />
            <p className="text-[10px] mt-1 text-[var(--fg-secondary)]">{c.name}</p>
            <code className="text-[10px] text-[var(--fg-tertiary)]">{c.hex}</code>
          </div>
        ))}
      </div>
      <div className="flex gap-2 items-end">
        <input id="color-hex" type="color" defaultValue="#3b82f6" className="w-10 h-10 rounded cursor-pointer" />
        <input id="color-name" type="text" placeholder="Color name" className="flex-1 h-9 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs" />
        <button onClick={handleAdd} className="px-3 h-9 rounded-lg gradient-bg text-white text-xs font-medium">Add</button>
      </div>
    </div>
  );
}
