'use client';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  created_at: string;
}

export function JobCard({ job }: { job: Job }) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    succeeded: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const statusColor = statusColors[job.status] || 'bg-gray-100 text-gray-800';

  return (
    <a
      href={`/jobs/${job.id}`}
      className="block p-4 border rounded hover:bg-gray-50 transition-colors"
    >
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg capitalize">{job.task_type.replace(/_/g, ' ')}</h3>
          <p className="text-sm text-gray-500">
            {new Date(job.created_at).toLocaleString('vi-VN')}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
          {job.status} ({job.progress}%)
        </span>
      </div>
    </a>
  );
}
