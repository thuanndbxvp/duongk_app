'use client';

import { useEffect, useState } from 'react';
import { ChannelList } from '@/components/channel-list';
import { ScrapeJobList } from '@/components/scrape-job-list';

export default function ChannelCollectorPage() {
  const [channels, setChannels] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/channel-collector/channels').then(r => r.json()),
      fetch('/api/channel-collector/jobs').then(r => r.json()),
    ]).then(([c, j]) => {
      setChannels(Array.isArray(c) ? c : c.channels || []);
      setJobs(Array.isArray(j) ? j : j.jobs || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = async () => {
    if (!url) return;
    await fetch('/api/channel-collector/channels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, name }),
    });
    setUrl(''); setName('');
    fetchData();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold">📺 Channel Collector</h1>

      <div className="glass-strong rounded-xl p-4 flex gap-3">
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="YouTube channel URL"
          className="flex-1 h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm focus:outline-none focus:border-[var(--brand-400)]" />
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Name (optional)"
          className="w-40 h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm" />
        <button onClick={handleAdd} className="px-4 h-10 rounded-lg gradient-bg text-white text-sm font-medium">Add</button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-3">Tracked Channels</h2>
          {loading ? <p className="text-xs text-[var(--fg-secondary)]">Loading...</p> : <ChannelList channels={channels} />}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-3">Recent Jobs</h2>
          {loading ? <p className="text-xs text-[var(--fg-secondary)]">Loading...</p> : <ScrapeJobList jobs={jobs} />}
        </div>
      </div>
    </div>
  );
}
