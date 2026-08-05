'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { IconPlus, IconArrowRight, IconAlert, IconChannels } from '@/components/icons';

export default function NewProjectPage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const response = await fetch('/api/channels/collect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ youtube_url: url }),
    });

    if (response.ok) {
      const data = await response.json();
      router.push(`/jobs/${data.job_id}`);
    } else {
      const err = await response.json();
      setError(err.detail || 'Có lỗi xảy ra');
    }
    setLoading(false);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
          <IconPlus size={14} /> New Project
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Tạo Channel Assistant</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Dán URL kênh YouTube — AppDK sẽ thu thập video và phân tích DNA phong cách.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative glass-strong rounded-2xl p-7 space-y-5 overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute -top-24 -right-24 h-56 w-56 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl"
        />

        <div className="relative space-y-1.5">
          <label htmlFor="url" className="block text-sm font-medium text-[var(--fg-secondary)]">
            YouTube Channel URL
          </label>
          <input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/@channel"
            required
            className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition"
          />
          <p className="text-xs text-[var(--fg-tertiary)]">
            Hỗ trợ @handle, /channel/, /c/, /user/.
          </p>
        </div>

        {error && (
          <div className="relative flex items-start gap-2 text-sm text-[var(--danger)] p-3 rounded-xl bg-[rgba(248,113,113,0.08)] border border-[rgba(248,113,113,0.2)]">
            <IconAlert size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-glow relative w-full h-12 rounded-xl text-sm font-semibold text-white inline-flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span className="relative inline-flex items-center justify-center gap-2 gradient-bg rounded-[10px] w-full h-12">
            <IconChannels size={16} />
            {loading ? 'Đang xử lý…' : 'Bắt đầu thu thập'}
            {!loading && <IconArrowRight size={16} />}
          </span>
        </button>
      </form>
    </div>
  );
}
