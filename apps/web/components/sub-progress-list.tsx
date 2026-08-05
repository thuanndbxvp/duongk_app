interface SubProgress {
  [key: string]: { status: string; progress: number };
}

export function SubProgressList({ subProgress }: { subProgress: SubProgress }) {
  if (!subProgress) return null;
  
  const entries = Object.entries(subProgress);

  return (
    <div className="space-y-3">
      {entries.map(([key, value]) => {
        let statusBg = 'bg-gray-100 text-gray-800';
        let barColor = 'bg-gray-400';
        
        if (value.status === 'done' || value.status === 'succeeded') {
          statusBg = 'bg-green-100 text-green-800';
          barColor = 'bg-green-500';
        } else if (value.status === 'running') {
          statusBg = 'bg-blue-100 text-blue-800';
          barColor = 'bg-blue-500';
        } else if (value.status === 'failed') {
          statusBg = 'bg-red-100 text-red-800';
          barColor = 'bg-red-500';
        }

        return (
          <div key={key} className="p-4 border rounded bg-white">
            <div className="flex justify-between items-center mb-3">
              <span className="capitalize font-medium text-gray-700">
                {key.replace(/_/g, ' ')}
              </span>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusBg}`}>
                {value.status} ({value.progress}%)
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div
                className={`${barColor} h-1.5 rounded-full transition-all duration-300`}
                style={{ width: `${value.progress}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
