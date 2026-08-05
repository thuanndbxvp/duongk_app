'use client';

import { useEffect, useState } from 'react';
import { SubProgressList } from '@/components/sub-progress-list';
import { ProgressBar } from '@/components/progress-bar';
import { subscribeToJobUpdates } from '@/lib/realtime';
import { useRouter } from 'next/navigation';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  sub_progress: Record<string, any>;
  result?: any;
}

export default function JobProgressPage({ params }: { params: Promise<{ id: string }> }) {
  const [job, setJob] = useState<Job | null>(null);
  const router = useRouter();

  useEffect(() => {
    let unsubscribe: () => void;

    async function init() {
      const resolvedParams = await params;

      // Initial fetch via our BFF
      fetch(`/api/jobs/${resolvedParams.id}`)
        .then((r) => r.json())
        .then(setJob);

      // Realtime subscription
      unsubscribe = subscribeToJobUpdates(resolvedParams.id, (newJob) => {
        setJob(newJob as Job);
      });
    }

    init();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [params]);

  if (!job) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );

  return (
    <main className="container mx-auto p-8 max-w-3xl mt-8 bg-white shadow rounded-lg border">
      <h1 className="text-3xl font-bold mb-6 capitalize border-b pb-4">
        {job.task_type.replace(/_/g, ' ')}
      </h1>
      
      <div className="mb-8 bg-gray-50 p-4 rounded border">
        <div className="flex justify-between mb-2 items-center">
          <span className="font-semibold text-gray-700">Tiến trình tổng</span>
          <span className="font-bold text-blue-600">{job.progress}%</span>
        </div>
        <ProgressBar progress={job.progress} barColor="bg-blue-600" height="h-3" />
        <div className="mt-4 flex justify-between items-center">
          <span className="text-sm font-medium text-gray-500 uppercase tracking-wider">Trạng thái: {job.status}</span>
          {job.status === 'succeeded' && job.result?.script_id && (
            <button 
              onClick={() => router.push(`/scripts/${job.result.script_id}`)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
            >
              Xem Kịch Bản
            </button>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Chi tiết các bước</h2>
        <SubProgressList subProgress={job.sub_progress} />
      </div>
    </main>
  );
}
