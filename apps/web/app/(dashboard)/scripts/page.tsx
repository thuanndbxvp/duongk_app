'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Script {
  id: string;
  title: string;
  status: string;
  quality_score: number | null;
  created_at: string;
}

export default function ScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/scripts')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setScripts(data);
        } else if (data.data) {
          setScripts(data.data);
        } else {
          setScripts([]);
        }
      })
      .catch(() => setError('Failed to load scripts'))
      .finally(() => setLoading(false));
  }, []);

  const getQualityBadge = (score: number | null) => {
    if (score === null) return <span className="text-gray-500">No score</span>;
    if (score >= 0.8) return <span className="text-green-400">High ({Math.round(score * 100)}%)</span>;
    if (score >= 0.5) return <span className="text-yellow-400">Medium ({Math.round(score * 100)}%)</span>;
    return <span className="text-red-400">Low ({Math.round(score * 100)}%)</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
            Scripts
          </div>
          <h1 className="text-3xl font-bold mt-2">My Scripts</h1>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-300)] border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && scripts.length === 0 && (
        <div className="text-center py-20">
          <p className="text-[var(--fg-secondary)]">No scripts yet</p>
          <p className="text-sm text-[var(--fg-tertiary)] mt-2">
            Scripts will appear here after being generated from projects
          </p>
        </div>
      )}

      {!loading && scripts.length > 0 && (
        <div className="grid gap-4">
          {scripts.map((script) => (
            <Link
              key={script.id}
              href={`/scripts/${script.id}`}
              className="block p-4 rounded-xl glass border border-[var(--glass-border)] hover:bg-[var(--surface-hover)] transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{script.title || 'Untitled Script'}</h3>
                  <p className="text-sm text-[var(--fg-secondary)] mt-1">
                    {new Date(script.created_at).toLocaleDateString('vi-VN')}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm">{getQualityBadge(script.quality_score)}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    script.status === 'completed' 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {script.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
