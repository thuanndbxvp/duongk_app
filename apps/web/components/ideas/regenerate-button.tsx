'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function RegenerateButton({ assistantId }: { assistantId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!confirm('Regenerate sẽ charge 5 credits. Tiếp tục?')) return;

    setLoading(true);
    try {
      const response = await fetch('/api/jobs/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          task_type: 'idea_generation',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/jobs/${data.job_id}`);
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
    >
      {loading ? 'Đang chạy...' : '🔄 Regenerate (5 credits)'}
    </button>
  );
}
