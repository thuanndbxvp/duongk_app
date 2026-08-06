'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { IconSparkle, IconArrowRight, IconAlert } from '@/components/icons';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    try {
      const text = await response.text();
      if (!response.ok) {
        try {
          const err = JSON.parse(text);
          setError(err.error || 'Đăng nhập thất bại');
        } catch {
          setError(text || `Lỗi máy chủ (${response.status})`);
        }
        return;
      }
      const data = JSON.parse(text);
      router.push(data.redirect || '/dashboard');
    } catch {
      setError('Không thể kết nối đến máy chủ');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh flex flex-col">
      <header className="px-8 py-5">
        <Link href="/" className="inline-flex items-center gap-2">
          <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-xl gradient-bg btn-glow">
            <IconSparkle size={16} className="text-white relative" />
          </span>
          <span className="font-bold text-lg gradient-text">AppDK</span>
        </Link>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md animate-fade-up">
          {/* Hero text */}
          <div className="text-center mb-8 space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">
              Chào mừng trở lại
            </h1>
            <p className="text-[var(--fg-secondary)]">
              Đăng nhập để tiếp tục tạo script viral.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="relative glass-strong rounded-2xl p-7 space-y-5 overflow-hidden">
            <div
              aria-hidden
              className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl"
            />

            {error && (
              <div className="relative flex items-start gap-2 text-sm text-[var(--danger)] p-3 rounded-xl bg-[rgba(248,113,113,0.08)] border border-[rgba(248,113,113,0.2)]">
                <IconAlert size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="relative space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-[var(--fg-secondary)]">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full h-11 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition"
              />
            </div>

            <div className="relative space-y-1.5">
              <label htmlFor="password" className="block text-sm font-medium text-[var(--fg-secondary)]">
                Mật khẩu
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full h-11 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-glow relative w-full h-11 rounded-xl text-sm font-semibold text-white inline-flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span className="relative inline-flex items-center justify-center gap-2 gradient-bg rounded-[10px] w-full h-11">
                {loading ? (
                  'Đang đăng nhập…'
                ) : (
                  <>
                    Đăng nhập <IconArrowRight size={16} />
                  </>
                )}
              </span>
            </button>

            <p className="relative text-center text-sm text-[var(--fg-tertiary)]">
              Chưa có tài khoản?{' '}
              <Link href="/pricing" className="text-[var(--brand-300)] hover:text-white font-medium">
                Xem gói giá
              </Link>
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
