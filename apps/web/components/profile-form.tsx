'use client';

import { useState } from 'react';
import { IconCheck } from '@/components/icons';

interface Props {
  initial: {
    email: string;
    full_name: string | null;
    avatar_url: string | null;
  };
}

export function ProfileForm({ initial }: Props) {
  const [fullName, setFullName] = useState(initial.full_name || '');
  const [avatarUrl, setAvatarUrl] = useState(initial.avatar_url || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const res = await fetch('/api/account/update-profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          avatar_url: avatarUrl,
        }),
      });

      if (res.ok) {
        setMessage({ ok: true, text: 'Đã lưu thay đổi' });
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage({ ok: false, text: err.error || 'Lỗi' });
      }
    } catch {
      setMessage({ ok: false, text: 'Không thể kết nối đến máy chủ' });
    } finally {
      setSaving(false);
    }
  }

  const inputClass =
    'w-full h-11 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition';

  return (
    <form onSubmit={handleSave} className="space-y-5">
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Email
        </label>
        <input
          type="email"
          value={initial.email}
          disabled
          className={`${inputClass} opacity-60 cursor-not-allowed`}
        />
        <p className="text-xs text-[var(--fg-tertiary)]">
          Email không thể thay đổi.
        </p>
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Họ và tên
        </label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Nguyễn Văn A"
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Avatar URL
        </label>
        <input
          type="url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          placeholder="https://..."
          className={inputClass}
        />
      </div>

      {message && (
        <div
          className={`flex items-start gap-2 text-sm p-3 rounded-xl border ${
            message.ok
              ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20'
              : 'text-[var(--danger)] bg-[rgba(248,113,113,0.08)] border-[rgba(248,113,113,0.2)]'
          }`}
        >
          {message.ok && <IconCheck size={16} className="mt-0.5 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={saving}
        className="btn-glow inline-flex items-center justify-center h-11 px-6 rounded-xl text-sm font-semibold text-white gradient-bg disabled:opacity-60 disabled:cursor-not-allowed hover:brightness-110 transition"
      >
        {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
      </button>
    </form>
  );
}