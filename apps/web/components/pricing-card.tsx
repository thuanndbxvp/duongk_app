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
      className={`relative bg-white rounded-lg shadow border p-6 ${
        popular ? 'border-blue-500 ring-2 ring-blue-200' : ''
      }`}
    >
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-bold">
          ⭐ POPULAR
        </span>
      )}

      <h3 className="text-2xl font-bold">{name}</h3>
      <p className="text-4xl font-bold mt-2">
        {price}
        <span className="text-sm text-gray-500 font-normal">/tháng</span>
      </p>

      <p className="text-sm text-gray-600 mt-2">
        💰 {credits} credits/tháng
      </p>

      <ul className="mt-4 space-y-2">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className="text-green-500">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        {isCurrent ? (
          <button
            disabled
            className="w-full bg-gray-200 text-gray-500 px-4 py-2 rounded cursor-not-allowed"
          >
            Plan hiện tại
          </button>
        ) : (
          <button
            onClick={handleUpgrade}
            className={`w-full px-4 py-2 rounded font-medium ${
              popular
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            {tier === 'enterprise' ? 'Liên hệ' : 'Upgrade'}
          </button>
        )}
      </div>
    </div>
  );
}
