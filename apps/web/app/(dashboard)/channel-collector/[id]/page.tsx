'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function ChannelDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [channel, setChannel] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/channel-collector/channels/${id}`)
      .then(r => r.json())
      .then(setChannel)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-2xl mx-auto py-12 animate-pulse text-[var(--fg-secondary)]">Loading...</div>;
  if (!channel) return <div className="max-w-2xl mx-auto py-12 text-red-400">Channel not found</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{channel.name || 'Channel'}</h1>
        <button onClick={async () => {
          await fetch(`/api/channel-collector/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel_id: id }),
          });
          alert('Re-scrape started');
        }} className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium">
          🔄 Re-scrape
        </button>
      </div>

      <div className="glass-strong rounded-2xl p-6 space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-[var(--fg-tertiary)]">URL</span><p className="font-medium text-xs break-all">{channel.url}</p></div>
          <div><span className="text-[var(--fg-tertiary)]">Added</span><p className="font-medium">{channel.created_at ? new Date(channel.created_at).toLocaleDateString('vi-VN') : '-'}</p></div>
        </div>

        {channel.recent_videos && channel.recent_videos.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mt-3 mb-2">Recent Videos</h3>
            <div className="space-y-1">
              {channel.recent_videos.slice(0, 10).map((v: any, i: number) => (
                <div key={i} className="text-xs text-[var(--fg-secondary)] p-1.5 rounded bg-white/[0.04]">{v.title || v.id}</div>
              ))}
            </div>
          </div>
        )}

        <button onClick={async () => {
          if (!confirm('Delete this channel?')) return;
          await fetch(`/api/channel-collector/channels/${id}`, { method: 'DELETE' });
          window.location.href = '/channel-collector';
        }} className="px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-xs">
          Delete Channel
        </button>
      </div>
    </div>
  );
}
