import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { PricingCard } from '@/components/pricing-card';

export default async function PricingPage() {
  const token = await getAccessToken();
  // Pricing có thể public, nhưng cần current tier để highlight
  let currentTier = 'free';

  if (token) {
    const res = await apiFetch('/api/credits/balance', {}, token);
    if (res.ok) {
      const data = await res.json();
      currentTier = data.tier;
    }
  }

  const tiers = [
    {
      tier: 'free' as const,
      name: 'Free',
      price: '$0',
      credits: 100,
      features: [
        'Validate niche',
        'Collect 50 videos',
        'Generate 2 scripts/month',
        'Basic support',
      ],
    },
    {
      tier: 'pro' as const,
      name: 'Pro',
      price: '$19',
      credits: 500,
      features: [
        'Tất cả Free features',
        'Deep Analysis đầy đủ 14 outputs',
        'Generate 20 scripts/month',
        'Idea Generation unlimited',
        'Email support',
        'Priority queue',
      ],
      popular: true,
    },
    {
      tier: 'enterprise' as const,
      name: 'Enterprise',
      price: 'Custom',
      credits: 5000,
      features: [
        'Tất cả Pro features',
        '5000 credits/tháng',
        'Dedicated support 24/7',
        'Custom integrations',
        'SLA 99.9%',
      ],
    },
  ];

  function handleUpgrade(tier: string) {
    if (tier === 'enterprise') {
      window.location.href = 'mailto:sales@appdk.vn';
    } else {
      alert(`Upgrade to ${tier} - Tính năng thanh toán đang phát triển`);
    }
  }

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-2">Choose Your Plan</h1>
        <p className="text-gray-600">
          Bắt đầu miễn phí, nâng cấp khi cần thiết
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {tiers.map((t) => (
          <PricingCard
            key={t.tier}
            tier={t.tier}
            name={t.name}
            price={t.price}
            credits={t.credits}
            features={t.features}
            currentTier={currentTier}
            popular={t.popular}
            onUpgrade={() => handleUpgrade(t.tier)}
          />
        ))}
      </div>
    </main>
  );
}
