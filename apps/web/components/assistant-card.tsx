import Link from 'next/link';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_subscribers: number;
  total_videos_collected: number;
  viral_videos_count: number;
  status: 'collecting' | 'ready' | 'failed';
  has_analysis: boolean;
  scripts_count: number;
  last_job_at: string | null;
  created_at: string;
}

export function AssistantCard({ assistant }: { assistant: Assistant }) {
  const statusColors = {
    ready: 'bg-green-100 text-green-800',
    collecting: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
  };

  const formatSubs = (n: number): string => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <Link
      href={`/assistants/${assistant.id}`}
      className="block bg-white border rounded-lg p-5 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start gap-4">
        <img
          src={assistant.channel_thumbnail || '/placeholder.png'}
          alt={assistant.channel_name}
          className="w-16 h-16 rounded-full object-cover"
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg truncate">{assistant.channel_name}</h3>
          <p className="text-sm text-gray-500">
            {formatSubs(assistant.channel_subscribers)} subscribers
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-800">
            {assistant.total_videos_collected}
          </div>
          <div className="text-xs text-gray-500">videos</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-orange-600">
            {assistant.viral_videos_count}
          </div>
          <div className="text-xs text-gray-500">viral</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">
            {assistant.scripts_count}
          </div>
          <div className="text-xs text-gray-500">scripts</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[assistant.status] || statusColors.collecting}`}>
          {assistant.status}
        </span>
        {assistant.has_analysis && (
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
            🧠 analyzed
          </span>
        )}
      </div>
    </Link>
  );
}
