'use client';

import { ReactNode, useEffect } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  requireText?: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Generic confirmation dialog. Glass styling consistent with admin pages.
 *
 * If `requireText` is set, the user must type that exact value into a
 * confirmation input before the Confirm button becomes enabled.
 * Used for destructive actions (delete user, etc.).
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  requireText,
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onCancel}
    >
      <ConfirmDialogBody
        title={title}
        description={description}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        danger={danger}
        requireText={requireText}
        busy={busy}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    </div>
  );
}

function ConfirmDialogBody({
  title,
  description,
  confirmLabel,
  cancelLabel,
  danger,
  requireText,
  busy,
  onConfirm,
  onCancel,
}: Omit<ConfirmDialogProps, 'open'>) {
  // State for requireText lives in a tiny uncontrolled input; we read on submit.
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (requireText) {
      const input = (e.currentTarget.elements.namedItem('confirm-text') as HTMLInputElement | null);
      if (input && input.value !== requireText) return;
    }
    onConfirm();
  };

  return (
    <form
      onClick={(e) => e.stopPropagation()}
      onSubmit={handleSubmit}
      className="glass-strong rounded-2xl p-6 w-full max-w-md space-y-4 animate-fade-up"
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      {description && (
        <div className="text-sm text-[var(--fg-secondary)]">{description}</div>
      )}
      {requireText && (
        <div className="space-y-2">
          <label className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">
            Type <span className="font-mono text-[var(--brand-300)]">{requireText}</span> to confirm
          </label>
          <input
            name="confirm-text"
            type="text"
            autoComplete="off"
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
          />
        </div>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="h-9 px-4 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)] hover:text-white disabled:opacity-50"
        >
          {cancelLabel}
        </button>
        <button
          type="submit"
          disabled={busy}
          className={`h-9 px-4 rounded-lg text-sm font-semibold text-white disabled:opacity-50 ${
            danger ? 'bg-red-500/80 hover:bg-red-500' : 'bg-[var(--brand-500)] hover:bg-[var(--brand-400)]'
          }`}
        >
          {busy ? 'Working…' : confirmLabel}
        </button>
      </div>
    </form>
  );
}
