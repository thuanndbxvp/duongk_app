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
    <div
      className={`relative glass-strong rounded-2xl p-6 overflow-hidden border-l-4 ${
        isLow ? 'border-l-[var(--danger)]' : 'border-l-emerald-400'
      }`}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -top-16 -right-16 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
      />
      <div className="relative space-y-3">
        <p className="text-sm text-[var(--fg-secondary)]">Credits còn lại</p>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-white">
            {credits.toLocaleString('vi-VN')}
          </span>
          {monthlyQuota ? (
            <span className="text-sm text-[var(--fg-tertiary)]">
              / {monthlyQuota.toLocaleString('vi-VN')}
            </span>
          ) : null}
        </div>

        {percentage !== null && (
          <div className="space-y-1.5">
            <div className="w-full bg-white/[0.06] rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all ${
                  percentage < 20
                    ? 'bg-gradient-to-r from-red-500 to-red-400'
                    : 'bg-gradient-to-r from-emerald-500 to-emerald-300'
                }`}
                style={{ width: `${Math.min(100, percentage)}%` }}
              />
            </div>
            <p className="text-xs text-[var(--fg-tertiary)]">
              {percentage}% còn lại
            </p>
          </div>
        )}

        {isLow && (
          <p className="text-xs text-[var(--danger)] font-medium">
            ⚠️ Sắp hết credits
          </p>
        )}
      </div>
    </div>
  );
}