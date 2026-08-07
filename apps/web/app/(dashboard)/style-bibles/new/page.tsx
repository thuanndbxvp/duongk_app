'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function NewStyleBiblePage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError('Name is required'); return; }
    setLoading(true); setError('');

    try {
      const r = await fetch('/api/style-bibles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (r.ok) {
        const data = await r.json();
        router.push(`/style-bibles/${data.id}`);
      } else {
        const err = await r.json();
        setError(err.detail || 'Failed to create');
      }
    } catch { setError('Cannot connect'); }
    setLoading(false);
  }

  return (
    <div className="max-w-xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">🎨 New Style Bible</h1>
      <form onSubmit={handleSubmit} className="glass-strong rounded-2xl p-6 space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--fg-secondary)]">Name *</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="My Style Bible"
            className="w-full h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--fg-secondary)]">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Mô tả..."
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--fg-secondary)]">Tags (comma separated)</label>
          <input type="text" value={tags} onChange={e => setTags(e.target.value)} placeholder="anime, cinematic"
            className="w-full h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full h-12 rounded-xl gradient-bg text-white font-semibold text-sm disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Style Bible'}
        </button>
      </form>
    </div>
  );
}
