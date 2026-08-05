interface Props {
  credits: number;
  tier: string;
  monthlyQuota?: number;
  lastTopup?: string;
}

export function CreditsCard({ credits, tier, monthlyQuota, lastTopup }: Props) {
  const isLow = credits < 20;
  const percentage = monthlyQuota
    ? Math.round((credits / monthlyQuota) * 100)
    : null;

  return (
    <div className={`bg-white rounded-lg shadow border-l-4 p-6 ${
      isLow ? 'border-red-500' : 'border-green-500'
    }`}>
      <p className="text-sm text-gray-500">Credits còn lại</p>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-4xl font-bold">{credits}</span>
        <span className="text-sm text-gray-500">
          {monthlyQuota ? `/ ${monthlyQuota}` : ''}
        </span>
      </div>
      {percentage !== null && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                percentage < 20 ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, percentage)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{percentage}% còn lại</p>
        </div>
      )}
      {isLow && (
        <p className="text-xs text-red-600 mt-2">⚠️ Sắp hết credits</p>
      )}
    </div>
  );
}
