'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function NewProjectPage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const response = await fetch('/api/projects/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ youtube_url: url }),
    });

    if (response.ok) {
      const data = await response.json();
      router.push(`/jobs/${data.job_id}`);
    } else {
      const errData = await response.json();
      setError(errData.error || errData.detail || 'Failed to start project');
    }
    setLoading(false);
  }

  return (
    <main className="container mx-auto p-8 max-w-2xl mt-12">
      <div className="bg-white p-8 rounded-lg shadow border">
        <h1 className="text-3xl font-bold mb-8">Dự án mới</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700">
              YouTube Channel URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/@channel"
              required
              className="w-full p-3 border rounded focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          {error && <p className="text-red-600 bg-red-50 p-3 rounded text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-medium px-4 py-3 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Đang xử lý...' : 'Bắt đầu tạo kịch bản'}
          </button>
        </form>
      </div>
    </main>
  );
}
