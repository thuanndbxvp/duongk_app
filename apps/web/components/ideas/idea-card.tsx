'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export function IdeaCard({
  idea,
  assistantId,
}: {
  idea: Idea;
  assistantId: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const gapColor =
    idea.gap_score >= 70
      ? 'bg-green-500'
      : idea.gap_score >= 40
      ? 'bg-yellow-500'
      : 'bg-red-500';

  const confidenceColor = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  }[idea.confidence];

  async function generateScript() {
    setLoading(true);
    try {
      const response = await fetch('/api/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          topic: idea.idea_topic,
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
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📌</span>
            <h3 className="text-xl font-bold">{idea.idea_topic}</h3>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`px-2 py-1 rounded-full font-bold text-white ${gapColor}`}>
              Gap: {idea.gap_score}
            </span>
            <span className={`px-2 py-1 rounded-full font-medium text-xs ${confidenceColor}`}>
              {idea.confidence.toUpperCase()}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
              Cluster {idea.cluster_id}
            </span>
          </div>
        </div>
      </div>

      {idea.related_topics && idea.related_topics.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-1">Related topics:</p>
          <div className="flex flex-wrap gap-1">
            {idea.related_topics.map((t, i) => (
              <span key={i} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">💡 Cơ hội:</span>{' '}
          {idea.opportunity_description}
        </p>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={generateScript}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Đang tạo...' : '✍️ Tạo Script (30 credits)'}
        </button>
      </div>
    </div>
  );
}
