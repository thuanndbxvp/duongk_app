'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface User {
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  tier: string;
  credits: number;
}

export function UserMenu({ user }: { user: User }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

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
        className="flex items-center gap-2 hover:bg-gray-100 rounded-full p-1 transition-colors"
        aria-label="User menu"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.email}
            className="w-8 h-8 rounded-full object-cover"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">
            {initials}
          </div>
        )}
        <span className="hidden md:inline text-sm">▼</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 bg-white border rounded-lg shadow-lg overflow-hidden z-50">
          {/* User info */}
          <div className="p-4 border-b bg-gray-50">
            <p className="font-semibold truncate">
              {user.full_name || user.email}
            </p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded uppercase">
                {user.tier}
              </span>
              <span className="text-gray-500">{user.credits} credits</span>
            </div>
          </div>

          {/* Menu items */}
          <div className="py-1">
            <Link
              href="/account/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100"
            >
              <span>👤</span>
              <span>Account Settings</span>
            </Link>
            <Link
              href="/billing"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100"
            >
              <span>💰</span>
              <span>Billing</span>
            </Link>
            <Link
              href="/pricing"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100"
            >
              <span>📈</span>
              <span>Pricing</span>
            </Link>
          </div>

          {/* Logout */}
          <div className="border-t">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2 hover:bg-red-50 text-red-600 w-full text-left"
            >
              <span>🔓</span>
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
