'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface AssistantActionsProps {
  assistantId: string;
  hasAnalysis: boolean;
  hasScripts: boolean;
}

export function AssistantActions({
  assistantId,
  hasAnalysis,
  hasScripts,
}: AssistantActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  async function triggerJob(taskType: string, redirectToJobs = true) {
    setLoading(taskType);
    try {
      const response = await fetch(`/api/jobs/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assistant_id: assistantId, task_type: taskType }),
      });

      if (response.ok) {
        const data = await response.json();
        if (redirectToJobs) {
          router.push(`/jobs/${data.job_id}`);
        } else {
          router.refresh();
        }
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to start job');
      }
    } finally {
      setLoading(null);
    }
  }

  const actions = [
    {
      id: 'analyze',
      label: 'Deep Analysis',
      emoji: '🧠',
      cost: 50,
      taskType: 'deep_analysis',
      disabled: false,
    },
    {
      id: 'ideas',
      label: 'Generate Ideas',
      emoji: '💡',
      cost: 5,
      taskType: 'idea_generation',
      disabled: !hasAnalysis,
      tooltip: !hasAnalysis ? 'Cần chạy Deep Analysis trước' : undefined,
    },
    {
      id: 'script',
      label: 'Generate Script',
      emoji: '✍️',
      cost: 30,
      taskType: 'script_generate',
      disabled: !hasAnalysis,
      tooltip: !hasAnalysis ? 'Cần chạy Deep Analysis trước' : undefined,
    },
    {
      id: 'history',
      label: 'Xem Scripts',
      emoji: '📜',
      cost: 0,
      taskType: 'history',
      disabled: !hasScripts,
      action: () => router.push(`/scripts?assistant_id=${assistantId}`),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {actions.map((action) => (
        <button
          key={action.id}
          disabled={action.disabled || loading === action.taskType}
          onClick={() => {
            if (action.taskType === 'history' && action.action) {
              action.action();
            } else {
              triggerJob(action.taskType);
            }
          }}
          title={action.tooltip}
          className="p-4 border-2 border-dashed rounded-lg hover:border-blue-500 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <div className="text-3xl mb-2">{action.emoji}</div>
          <div className="font-semibold">{action.label}</div>
          {action.cost > 0 && (
            <div className="text-xs text-gray-500 mt-1">{action.cost} credits</div>
          )}
          {loading === action.taskType && (
            <div className="text-xs text-blue-600 mt-1">Đang xử lý...</div>
          )}
        </button>
      ))}
    </div>
  );
}
