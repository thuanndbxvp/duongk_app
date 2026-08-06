'use client';

import { useEffect, useState } from 'react';
import { Select } from '@/components/select';

interface CreateUserModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (user: { id: string; email: string }) => void;
}

interface FormState {
  email: string;
  full_name: string;
  tier: 'free' | 'pro' | 'enterprise';
  credits: number;
  max_assistants: number;
}

const TIER_DEFAULTS: Record<FormState['tier'], { credits: number; max_assistants: number }> = {
  free:       { credits: 0,    max_assistants: 5 },
  pro:        { credits: 1000, max_assistants: 20 },
  enterprise: { credits: 5000, max_assistants: 100 },
};

const EMPTY: FormState = {
  email: '',
  full_name: '',
  tier: 'free',
  ...TIER_DEFAULTS.free,
};

export function CreateUserModal({ open, onClose, onCreated }: CreateUserModalProps) {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setForm(EMPTY);
      setError(null);
      setBusy(false);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
        return;
      }
      onCreated(data);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Create user"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="glass-strong rounded-2xl p-6 w-full max-w-md space-y-4 animate-fade-up"
      >
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Create user</h2>
          <p className="text-xs text-[var(--fg-tertiary)]">
            Creates auth.users + public.users rows. No invite email is sent.
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}

        <Field label="Email *">
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
            placeholder="user@example.com"
          />
        </Field>

        <Field label="Full name">
          <input
            type="text"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
            placeholder="Nguyen Van A"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Tier">
            <Select
              value={form.tier}
              onChange={(v) => {
                const tier = v as FormState['tier'];
                const defaults = TIER_DEFAULTS[tier];
                setForm({
                  ...form,
                  tier,
                  credits: defaults.credits,
                  max_assistants: defaults.max_assistants,
                });
              }}
              options={[
                { value: 'free', label: 'Free' },
                { value: 'pro', label: 'Pro' },
                { value: 'enterprise', label: 'Enterprise' },
              ]}
            />
          </Field>
          <Field label="Max assistants">
            <input
              type="number"
              min={0}
              max={1000}
              value={form.max_assistants}
              onChange={(e) => setForm({ ...form, max_assistants: Number(e.target.value) })}
              className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
            />
          </Field>
        </div>

        <Field label="Initial credits">
          <input
            type="number"
            min={0}
            value={form.credits}
            onChange={(e) => setForm({ ...form, credits: Number(e.target.value) })}
            className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
          />
          <span className="text-[10px] text-[var(--fg-tertiary)]">
            Auto-filled from tier. Override nếu cần.
          </span>
        </Field>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="h-9 px-4 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)] hover:text-white disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={busy || !form.email}
            className="h-9 px-4 rounded-lg bg-[var(--brand-500)] text-sm font-semibold text-white hover:bg-[var(--brand-400)] disabled:opacity-50"
          >
            {busy ? 'Creating…' : 'Create user'}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">{label}</span>
      {children}
    </label>
  );
}
