'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export function CreditsBadge() {
  const [credits, setCredits] = useState<number | null>(null);
  const [tier, setTier] = useState<string>('free');

  useEffect(() => {
    async function fetchBalance() {
      try {
        const res = await fetch('/api/credits/balance');
        if (res.ok) {
          const data = await res.json();
          setCredits(data.credits);
          setTier(data.tier);
        }
      } catch (e) {
        // Silent fail - badge hidden if can't fetch
      }
    }
    fetchBalance();
    // Refresh every 30s
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  if (credits === null) return null;

  const isLow = credits < 20;
  const colorClass = isLow
    ? 'bg-red-100 text-red-800 border-red-300'
    : 'bg-green-100 text-green-800 border-green-300';

  return (
    <Link
      href="/billing"
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClass} hover:shadow transition-shadow text-sm font-medium`}
    >
      <span>💰</span>
      <span>{credits} credits</span>
      <span className="text-xs opacity-70">({tier})</span>
      {isLow && <span>⚠️</span>}
    </Link>
  );
}
