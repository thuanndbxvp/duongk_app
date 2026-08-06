'use client';

import { useState } from 'react';

interface Props { projectIds?: string[]; }

export function BatchPlanner({ projectIds = [] }: Props) {
  const [name, setName] = useState('');
  const [taskType, setTaskType] = useState('render_draft');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleCreate() {
    setLoading(true);
    const res = await fetch('/api/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, project_ids: projectIds, task_type: taskType }),
    });
    const data = await res.json();
    if (res.ok) {
      setResult(`✅ Batch created: ${data.id} — ${data.total_items} items, ${data.total_cost_estimate} credits`);
    }
    setLoading(false);
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Batch name"
          className="flex-1 h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm" />
        <select value={taskType} onChange={e => setTaskType(e.target.value)}
          className="h-10 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-sm">
          <option value="render_draft">Draft Render</option>
          <option value="render_final">Final Render</option>
          <option value="thumbnail_generation">Thumbnails</option>
        </select>
        <button onClick={handleCreate} disabled={loading}
          className="px-4 h-10 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
          {loading ? '...' : 'Create Batch'}
        </button>
      </div>
      {result && <p className="text-sm text-green-400">{result}</p>}
    </div>
  );
}
