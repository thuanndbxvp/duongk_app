'use client';

interface Props {
  tier: 'free' | 'pro' | 'enterprise';
  name: string;
  price: string;
  credits: number;
  features: string[];
  currentTier: string;
  popular?: boolean;
}

export function PricingCard({
  tier,
  name,
  price,
  credits,
  features,
  currentTier,
  popular,
}: Props) {
  const isCurrent = currentTier === tier;

  function handleUpgrade() {
    if (tier === 'enterprise') {
      window.location.href = 'mailto:sales@appdk.vn';
    } else {
      alert(`Upgrade to ${tier} - Tính năng thanh toán đang phát triển`);
    }
  }

  return (
    <div
      className={`relative bg-[#1f2937] text-white rounded-xl shadow border p-6 transition-all ${
        popular ? 'border-[#3b82f6] ring-2 ring-[#3b82f6]/30' : 'border-[#374151]'
      }`}
    >
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#3b82f6] text-white px-4 py-1 rounded-full text-xs font-bold shadow-lg">
          ⭐ POPULAR
        </span>
      )}

      <h3 className="text-2xl font-bold">{name}</h3>
      <p className="text-4xl font-bold mt-2">
        {price}
        <span className="text-sm text-[#9ca3af] font-normal">/tháng</span>
      </p>

      <p className="text-sm text-[#9ca3af] mt-2">
        💰 {credits} credits/tháng
      </p>

      <ul className="mt-5 space-y-3">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-[#f9fafb]">
            <span className="text-[#10b981]">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-8">
        {isCurrent ? (
          <button
            disabled
            className="w-full bg-[#374151] text-[#9ca3af] px-4 py-3 rounded-lg cursor-not-allowed font-medium"
          >
            Plan hiện tại
          </button>
        ) : (
          <button
            onClick={handleUpgrade}
            className={`w-full px-4 py-3 rounded-lg font-semibold transition-colors ${
              popular
                ? 'bg-[#3b82f6] text-white hover:bg-[#2563eb]'
                : 'bg-[#374151] text-white hover:bg-[#4b5563]'
            }`}
          >
            {tier === 'enterprise' ? 'Liên hệ' : 'Nâng cấp ngay'}
          </button>
        )}
      </div>
    </div>
  );
}
