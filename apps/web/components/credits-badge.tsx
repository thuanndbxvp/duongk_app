'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { IconAlert, IconSparkle } from '@/components/icons';

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
      } catch {
        /* silent */
      }
    }
    fetchBalance();
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  if (credits === null) return null;

  const isLow = credits < 20;

  return (
    <Link
      href="/billing"
      className={`group relative inline-flex items-center gap-2 px-3 h-9 rounded-xl text-sm font-semibold transition-all duration-200 glass glass-hover ${
        isLow ? 'text-[var(--danger)]' : 'text-white'
      }`}
    >
      <IconSparkle size={14} className={isLow ? 'text-[var(--danger)]' : 'text-[var(--brand-300)]'} />
      <span className="tabular-nums">{credits.toLocaleString('vi-VN')}</span>
      <span className="text-[10px] uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">
        {tier}
      </span>
      {isLow && <IconAlert size={14} className="text-[var(--danger)]" />}
    </Link>
  );
}
