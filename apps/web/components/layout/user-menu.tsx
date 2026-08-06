'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { IconLogout, IconUser, IconBilling, IconChart, IconShield, IconDashboard } from '@/components/icons';

interface User {
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  tier: string;
  credits: number;
  role: string;
}

export function UserMenu({ user }: { user: User }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const pathname = usePathname();
  const isAdminRoute = pathname?.startsWith('/admin') ?? false;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
  }

  const initials = user.full_name
    ? user.full_name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : user.email.slice(0, 2).toUpperCase();

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-full p-1 transition-all hover:bg-white/[0.06]"
        aria-label="User menu"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.email}
            className="w-8 h-8 rounded-full object-cover"
          />
        ) : (
          <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-full gradient-bg text-white text-xs font-bold btn-glow">
            {initials}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-3 w-72 glass-strong rounded-2xl overflow-hidden z-50 animate-fade-up shadow-2xl">
          {/* Glow accent */}
          <div
            aria-hidden
            className="pointer-events-none absolute -top-12 -right-12 h-32 w-32 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl"
          />

          {/* User info */}
          <div className="relative px-4 py-4 border-b border-[var(--glass-border)]">
            <div className="flex items-center gap-3">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.email}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full gradient-bg text-white text-sm font-bold btn-glow">
                  {initials}
                </span>
              )}
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-white text-sm truncate">
                  {user.full_name || user.email}
                </p>
                <p className="text-xs text-[var(--fg-tertiary)] truncate">{user.email}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[rgba(196,181,253,0.12)] text-[#c4b5fd] text-[10px] font-semibold uppercase tracking-wider">
                {user.tier}
              </span>
              <span className="text-xs text-[var(--fg-secondary)]">
                {user.credits.toLocaleString()} credits
              </span>
            </div>
          </div>

          {/* Menu items */}
          <div className="relative py-1.5">
            <Link
              href="/account/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05] transition-colors"
            >
              <IconUser size={16} className="text-[var(--fg-tertiary)]" />
              <span>Account Settings</span>
            </Link>
            <Link
              href="/billing"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05] transition-colors"
            >
              <IconBilling size={16} className="text-[var(--fg-tertiary)]" />
              <span>Billing</span>
            </Link>
            <Link
              href="/pricing"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05] transition-colors"
            >
              <IconChart size={16} className="text-[var(--fg-tertiary)]" />
              <span>Pricing</span>
            </Link>
            {(user.role === 'admin' || user.role === 'super_admin') && (
              <>
                <div className="my-1.5 mx-3 border-t border-[var(--glass-border)]" />
                {isAdminRoute && (
                  <Link
                    href="/dashboard"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--fg-secondary)] hover:text-white hover:bg-white/[0.05] transition-colors"
                  >
                    <IconDashboard size={16} className="text-[var(--fg-tertiary)]" />
                    <span>Về Dashboard</span>
                    <span className="ml-auto text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/5 text-[var(--fg-tertiary)]">
                      {user.tier}
                    </span>
                  </Link>
                )}
                <Link
                  href="/admin"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-[#c4b5fd] hover:bg-[rgba(196,181,253,0.1)] transition-colors"
                >
                  <IconShield size={16} className="text-[#c4b5fd]" />
                  <span className="font-semibold">Admin Panel</span>
                  <span className="ml-auto text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#c4b5fd]/20 text-[#c4b5fd]">
                    {user.role === 'super_admin' ? 'Super' : 'Admin'}
                  </span>
                </Link>
              </>
            )}
          </div>

          {/* Logout */}
          <div className="relative border-t border-[var(--glass-border)] py-1.5">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--fg-secondary)] hover:text-[var(--danger)] hover:bg-[rgba(248,113,113,0.06)] transition-colors w-full text-left"
            >
              <IconLogout size={16} className="text-[var(--fg-tertiary)]" />
              <span>Đăng xuất</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
