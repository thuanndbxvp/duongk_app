'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS, isActiveRoute } from '@/lib/navigation';
import { IconSparkle, IconShield } from '@/components/icons';

export function Sidebar({ userRole = 'user' }: { userRole?: string }) {
  const pathname = usePathname();
  const mainItems = NAV_ITEMS.filter((i) => i.group === 'main');
  const accountItems = NAV_ITEMS.filter((i) => i.group === 'account');
  const isAdmin = userRole === 'admin' || userRole === 'super_admin';

  return (
    <nav className="h-full flex flex-col overflow-y-auto">
      <div className="px-3 py-5">
        {/* Main Tools */}
        <div className="mb-6">
          <h3 className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--fg-tertiary)]">
            Tools
          </h3>
          <div className="space-y-1">
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
                      ? 'bg-white/[0.07] text-white shadow-[inset_0-1px_0_rgba(255,255,255,0.08)]'
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
        </div>

        {/* Admin Panel */}
        {isAdmin && (
          <div className="mb-6">
            <div className="my-3 mx-2 border-t border-[var(--divider)]" />
            <Link
              href="/admin"
              className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                pathname.startsWith('/admin')
                  ? 'bg-[rgba(196,181,253,0.12)] text-white'
                  : 'text-[#c4b5fd] hover:bg-[rgba(196,181,253,0.08)] hover:text-white'
              }`}
            >
              {pathname.startsWith('/admin') && (
                <span
                  aria-hidden
                  className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-[3px] rounded-r-full bg-gradient-to-b from-[#c4b5fd] via-[#8b5cf6] to-[#ec4899]"
                />
              )}
              <IconShield size={18} className="text-[#c4b5fd]" />
              <span>Admin Panel</span>
              <span className="ml-auto text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#c4b5fd]/20 text-[#c4b5fd] font-semibold">
                {userRole === 'super_admin' ? 'Super' : 'Admin'}
              </span>
            </Link>
          </div>
        )}

        {/* Account */}
        <div className="mt-4 pt-4 border-t border-[var(--divider)]">
          <h3 className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--fg-tertiary)]">
            Account
          </h3>
          <div className="space-y-1">
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
        </div>
      </div>

      {/* Pro upsell card */}
      <div className="mx-3 mb-4 mt-auto rounded-2xl p-4 gradient-border bg-gradient-to-br from-[#1a1530] to-[#0f0b1c]">
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
