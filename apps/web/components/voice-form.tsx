'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Provider {
  id: string;
  name: string;
  languages: string[];
  supports_clone: boolean;
  requires_sample: boolean;
}

export function VoiceForm() {
  const router = useRouter();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [name, setName] = useState('');
  const [providerId, setProviderId] = useState('');
  const [language, setLanguage] = useState('');
  const [gender, setGender] = useState('male');
  const [sample, setSample] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/voices/providers')
      .then(r => r.json())
      .then(d => { setProviders(d.providers || []); if (d.providers?.[0]) setProviderId(d.providers[0].id); })
      .catch(() => {});
  }, []);

  const selected = providers.find(p => p.id === providerId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError('Name is required'); return; }
    if (selected?.requires_sample && !sample) { setError('Sample audio is required for this provider'); return; }
    if (sample && sample.size > 10 * 1024 * 1024) { setError('File too large (max 10MB)'); return; }

    setLoading(true);
    setError('');

    const fd = new FormData();
    fd.append('name', name);
    fd.append('provider_id', providerId);
    fd.append('language', language || (selected?.languages[0] || 'vi-VN'));
    fd.append('gender', gender);
    if (sample) fd.append('sample', sample);

    try {
      const r = await fetch('/api/voices', { method: 'POST', body: fd });
      if (r.ok) {
        const data = await r.json();
        router.push(`/voice-profiles/${data.id}`);
      } else {
        const err = await r.json();
        setError(err.detail || 'Failed to create voice');
      }
    } catch { setError('Cannot connect to server'); }
    setLoading(false);
  }

  return (
    <form onSubmit={handleSubmit} className="glass-strong rounded-2xl p-6 space-y-5 max-w-xl">
      <h2 className="text-lg font-semibold">Create Voice Profile</h2>

      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--fg-secondary)]">Name</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="My Voice"
          className="w-full h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--fg-secondary)]">Provider</label>
        <select value={providerId} onChange={e => { setProviderId(e.target.value); setLanguage(''); }}
          className="w-full h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]">
          {providers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {selected && (
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--fg-secondary)]">Language</label>
          <select value={language || selected.languages[0]} onChange={e => setLanguage(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]">
            {selected.languages.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      )}

      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--fg-secondary)]">Gender</label>
        <div className="flex gap-4">
          {['male', 'female'].map(g => (
            <label key={g} className="flex items-center gap-2 text-sm text-[var(--fg-secondary)]">
              <input type="radio" name="gender" value={g} checked={gender === g} onChange={() => setGender(g)} />
              {g === 'male' ? '👨 Male' : '👩 Female'}
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--fg-secondary)]">
          Sample Audio {selected?.requires_sample ? '*' : '(optional)'} — MP3/WAV, max 10MB
        </label>
        <input type="file" accept=".mp3,.wav,audio/mpeg,audio/wav"
          onChange={e => setSample(e.target.files?.[0] || null)}
          className="w-full text-sm text-[var(--fg-secondary)] file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:bg-[var(--brand-500)] file:text-white" />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button type="submit" disabled={loading}
        className="w-full h-12 rounded-xl gradient-bg text-white font-semibold text-sm disabled:opacity-50">
        {loading ? 'Creating...' : 'Create Voice'}
      </button>
    </form>
  );
}
