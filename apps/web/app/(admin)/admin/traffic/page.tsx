'use client';

import { useEffect, useState } from 'react';
import { TrafficChart } from '@/components/admin/traffic-chart';

export default function AdminTrafficPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/admin/traffic')
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">📊 Traffic Analytics</h1>
      {loading ? <p className="text-xs text-[var(--fg-secondary)] animate-pulse">Loading...</p> : <TrafficChart data={data} />}
    </div>
  );
}
