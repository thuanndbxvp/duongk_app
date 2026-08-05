'use client';

import { useEffect, useState } from 'react';
import { createBrowserClient } from '@supabase/ssr';
import { SubProgressList } from '@/components/sub-progress-list';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  sub_progress: Record<string, any>;
}

export default function JobProgressPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );

    // Initial fetch
    fetch(`/api/jobs/${params.id}`)
      .then((r) => r.json())
      .then(setJob);

    // Realtime subscription
    const channel = supabase
      .channel(`job-${params.id}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'jobs',
        filter: `id=eq.${params.id}`,
      }, (payload) => {
        setJob(payload.new as Job);
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [params.id]);

  if (!job) return <div>Loading...</div>;

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">{job.task_type}</h1>
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span>Tiến trình tổng</span>
          <span>{job.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>
      <SubProgressList subProgress={job.sub_progress} />
    </main>
  );
}
