'use client';

interface Ref { id: string; name: string; image_url?: string }

export function BackgroundRefs({ refs, onAdd }: { refs: Ref[]; onAdd: (name: string) => void }) {
  const handleAdd = () => {
    const name = (document.getElementById('bg-name') as HTMLInputElement)?.value || '';
    if (name) onAdd(name);
  };

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        {refs.map(r => (
          <div key={r.id} className="text-center p-2 rounded-lg bg-white/[0.04]">
            <div className="w-full aspect-video rounded-lg bg-white/[0.06] flex items-center justify-center text-xl mb-1">
              {r.image_url ? <img src={r.image_url} alt={r.name} className="w-full h-full object-cover rounded-lg" /> : '🏞️'}
            </div>
            <p className="text-[10px] text-[var(--fg-secondary)]">{r.name}</p>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input id="bg-name" type="text" placeholder="Background name" className="flex-1 h-9 px-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs" />
        <button onClick={handleAdd} className="px-3 h-9 rounded-lg gradient-bg text-white text-xs font-medium">Add</button>
      </div>
    </div>
  );
}
