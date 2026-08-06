'use client';

import { useEffect, useRef, useState } from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

interface Props {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  /** When true, popup fills trigger width; otherwise uses min-w-content. */
  matchWidth?: boolean;
}

function ChevronDown({ className = '' }: { className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export function Select({
  value,
  onChange,
  options,
  placeholder = 'Select…',
  className = '',
  matchWidth = true,
}: Props) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const current = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div ref={wrapRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`w-full h-9 px-3 pr-9 rounded-lg bg-[var(--bg-surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-primary)] text-left flex items-center gap-2 transition-colors hover:border-[var(--glass-border-strong)] focus:outline-none focus:border-[var(--brand-400)] ${open ? 'border-[var(--brand-400)]' : ''}`}
      >
        <span className="truncate flex-1">
          {current ? current.label : <span className="text-[var(--fg-tertiary)]">{placeholder}</span>}
        </span>
        <ChevronDown
          className={`absolute right-3 w-4 h-4 text-[var(--fg-tertiary)] transition-transform ${open ? 'rotate-180 text-[var(--brand-300)]' : ''}`}
        />
      </button>

      {open && (
        <div
          className={`absolute z-50 mt-1 ${matchWidth ? 'w-full left-0' : 'min-w-[180px] left-0'} max-h-60 overflow-auto rounded-lg bg-[var(--bg-elevated)] border border-[var(--glass-border-strong)] shadow-2xl shadow-black/40`}
        >
          <ul className="py-1">
            {options.map((opt) => {
              const isActive = opt.value === value;
              return (
                <li key={opt.value}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(opt.value);
                      setOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-sm text-left flex items-center gap-2 transition-colors ${
                      isActive
                        ? 'bg-[var(--brand-500)]/15 text-[var(--brand-300)]'
                        : 'text-[var(--fg-primary)] hover:bg-[var(--surface-hover)]'
                    }`}
                  >
                    <span className="flex-1 truncate">{opt.label}</span>
                    {isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-400)]" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}