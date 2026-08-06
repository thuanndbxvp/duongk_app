'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS, isActiveRoute } from '@/lib/navigation';
import { IconSparkle } from '@/components/icons';

export function Sidebar() {
  const pathname = usePathname();
  const mainItems = NAV_ITEMS.filter((i) => i.group === 'main');
  const accountItems = NAV_ITEMS.filter((i) => i.group === 'account');

  return (
    <nav className="h-full flex flex-col px-3 py-5">
      <div className="flex-1 space-y-1">
        {mainItems.map((item) => {
          const active = isActiveRoute(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              target={item.href.startsWith('http') ? '_blank' : undefined}
              className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                active
                  ? 'bg-white/[0.07] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'
                  : 'text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {active && (
                <span
                  aria-hidden
                  className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-[3px] rounded-r-full bg-gradient-to-b from-[#c4b5fd] via-[#8b5cf6] to-[#ec4899]"
                />
              )}
              <Icon
                size={18}
                className={active ? 'text-[#c4b5fd]' : 'text-[var(--fg-tertiary)] group-hover:text-white'}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-[var(--divider)] space-y-1">
        {accountItems.map((item) => {
          const active = isActiveRoute(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                active
                  ? 'bg-white/[0.07] text-white'
                  : 'text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Icon size={18} className={active ? 'text-[#c4b5fd]' : 'text-[var(--fg-tertiary)] group-hover:text-white'} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Pro upsell card */}
      <div className="mt-4 rounded-2xl p-4 gradient-border bg-gradient-to-br from-[#1a1530] to-[#0f0b1c]">
        <div className="flex items-center gap-2 text-[var(--brand-300)] text-xs font-semibold uppercase tracking-wider">
          <IconSparkle size={14} /> Upgrade
        </div>
        <p className="mt-2 text-sm font-semibold text-white leading-snug">
          Mở khóa script không giới hạn
        </p>
        <p className="mt-1 text-xs text-[var(--fg-tertiary)]">
          249K/tháng — viral mỗi tuần.
        </p>
      </div>
    </nav>
  );
}
