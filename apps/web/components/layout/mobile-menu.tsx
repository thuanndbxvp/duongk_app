'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS, isActiveRoute } from '@/lib/navigation';
import { IconClose, IconMenu, IconLogout } from '@/components/icons';

export function MobileMenu() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden inline-flex items-center justify-center h-10 w-10 rounded-xl text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05] transition"
        aria-label="Mở menu"
      >
        <IconMenu size={20} />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-40 lg:hidden bg-black/60 backdrop-blur-sm animate-fade-up"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      <div
        className={`fixed top-0 left-0 h-full w-72 z-50 lg:hidden transform transition-transform duration-300 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full glass-strong border-r border-[var(--glass-border)] flex flex-col">
          <div className="px-5 h-[68px] flex items-center justify-between border-b border-[var(--divider)]">
            <span className="font-bold text-lg gradient-text">AppDK</span>
            <button
              onClick={() => setOpen(false)}
              className="inline-flex items-center justify-center h-9 w-9 rounded-lg text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05]"
              aria-label="Đóng menu"
            >
              <IconClose size={18} />
            </button>
          </div>

          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {NAV_ITEMS.map((item) => {
              const active = isActiveRoute(pathname, item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                    active
                      ? 'bg-white/[0.07] text-white'
                      : 'text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon size={18} className={active ? 'text-[#c4b5fd]' : 'text-[var(--fg-tertiary)]'} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="p-3 border-t border-[var(--divider)]">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-[var(--fg-secondary)] hover:text-[var(--danger)] hover:bg-[rgba(248,113,113,0.06)] w-full transition"
            >
              <IconLogout size={18} />
              <span>Đăng xuất</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
