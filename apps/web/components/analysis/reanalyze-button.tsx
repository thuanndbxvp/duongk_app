'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function ReanalyzeButton({ assistantId }: { assistantId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!confirm('Re-analyze sẽ charge 50 credits. Tiếp tục?')) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/analysis/${assistantId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/jobs/${data.job_id}`);
      } else {
        const err = await response.json();
        alert(err.detail || err.error || 'Failed');
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
      {loading ? 'Đang chạy...' : '🔄 Re-analyze (50 credits)'}
    </button>
  );
}
