'use client';

import { useState } from 'react';
import { IconCheck } from '@/components/icons';

export function PasswordForm() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (newPassword.length < 8) {
      setMessage({ ok: false, text: 'Mật khẩu mới phải có ít nhất 8 ký tự' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage({ ok: false, text: 'Mật khẩu xác nhận không khớp' });
      return;
    }

    setSaving(true);

    try {
      const res = await fetch('/api/account/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      if (res.ok) {
        setMessage({ ok: true, text: 'Đã đổi mật khẩu' });
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
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
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Mật khẩu hiện tại
        </label>
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
          placeholder="••••••••"
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Mật khẩu mới
        </label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={8}
          placeholder="Tối thiểu 8 ký tự"
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-[var(--fg-secondary)]">
          Xác nhận mật khẩu mới
        </label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          placeholder="Nhập lại mật khẩu mới"
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
        {saving ? 'Đang cập nhật...' : 'Đổi mật khẩu'}
      </button>
    </form>
  );
}