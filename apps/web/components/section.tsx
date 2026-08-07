'use client';

import { ReactNode } from 'react';

interface Props {
  title: string;
  children: ReactNode;
  onAdd?: () => void;
}

export function Section({ title, children, onAdd }: Props) {
  return (
    <div className="glass-strong rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{title}</h3>
        {onAdd && (
          <button onClick={onAdd} className="text-xs px-2 py-1 rounded bg-white/[0.06] border border-[var(--glass-border)] text-[var(--fg-secondary)] hover:text-white">
            + Add
          </button>
        )}
      </div>
      {children}
    </div>
  );
}
