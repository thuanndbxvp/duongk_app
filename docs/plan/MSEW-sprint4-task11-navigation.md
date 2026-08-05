# Sprint 4+ Task Group 11: Navigation - MSEW

## Checklist

- [ ] Bước 1: lib/navigation.ts (nav config)
- [ ] Bước 2: components/layout/sidebar.tsx
- [ ] Bước 3: components/layout/user-menu.tsx
- [ ] Bước 4: components/layout/mobile-menu.tsx
- [ ] Bước 5: components/layout/breadcrumbs.tsx
- [ ] Bước 6: components/layout/topbar.tsx
- [ ] Bước 7: components/layout/authenticated-layout.tsx
- [ ] Bước 8: app/(dashboard)/layout.tsx
- [ ] Bước 9: Update app/layout.tsx
- [ ] Bước 10: Verify

---

## Bước 1: Navigation Config

**File:** `apps/web/lib/navigation.ts`

```typescript
export interface NavItem {
  href: string;
  label: string;
  icon: string;
  group?: 'main' | 'account';
}

export const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊', group: 'main' },
  { href: '/assistants', label: 'Channels', icon: '📺', group: 'main' },
  { href: '/projects/new', label: 'New Project', icon: '➕', group: 'main' },
  { href: '/billing', label: 'Billing', icon: '💰', group: 'main' },
  { href: '/account/settings', label: 'Account', icon: '👤', group: 'account' },
  { href: '/pricing', label: 'Pricing', icon: '📈', group: 'account' },
];

export function isActiveRoute(pathname: string, href: string): boolean {
  if (href === '/dashboard' && pathname === '/dashboard') return true;
  if (href === '/dashboard') return false; // Don't highlight on other routes
  return pathname === href || pathname.startsWith(href + '/');
}
```

---

## Bước 2: Sidebar

**File:** `apps/web/components/layout/sidebar.tsx`

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS, isActiveRoute } from '@/lib/navigation';

export function Sidebar() {
  const pathname = usePathname();
  const mainItems = NAV_ITEMS.filter((i) => i.group === 'main');
  const accountItems = NAV_ITEMS.filter((i) => i.group === 'account');

  return (
    <nav className="h-full p-4 flex flex-col">
      <div className="flex-1 space-y-1">
        {mainItems.map((item) => {
          const active = isActiveRoute(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
              {active && (
                <span className="ml-auto w-1.5 h-1.5 bg-blue-600 rounded-full" />
              )}
            </Link>
          );
        })}
      </div>

      <div className="border-t pt-4 mt-4 space-y-1">
        {accountItems.map((item) => {
          const active = isActiveRoute(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="border-t pt-4 mt-4">
        <LogoutButton />
      </div>
    </nav>
  );
}

function LogoutButton() {
  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  }

  return (
    <button
      onClick={handleLogout}
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-red-600 hover:bg-red-50 transition-colors w-full"
    >
      <span className="text-xl">🔓</span>
      <span>Logout</span>
    </button>
  );
}
```

---

## Bước 3: User Menu

**File:** `apps/web/components/layout/user-menu.tsx`

```typescript
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
```

---

## Bước 4: Mobile Menu

**File:** `apps/web/components/layout/mobile-menu.tsx`

```typescript
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS, isActiveRoute } from '@/lib/navigation';

export function MobileMenu() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden p-2 hover:bg-gray-100 rounded"
        aria-label="Open menu"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" strokeWidth="2" />
        </svg>
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Slide-in panel */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-white z-50 transform transition-transform duration-300 lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 border-b flex items-center justify-between">
          <span className="font-bold text-xl text-blue-600">AppDK</span>
          <button
            onClick={() => setOpen(false)}
            className="p-2 hover:bg-gray-100 rounded"
          >
            ✕
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = isActiveRoute(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
                  active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 w-full mt-4 border-t pt-4"
          >
            <span className="text-xl">🔓</span>
            <span>Logout</span>
          </button>
        </nav>
      </div>
    </>
  );
}
```

---

## Bước 5: Breadcrumbs

**File:** `apps/web/components/layout/breadcrumbs.tsx`

```typescript
import Link from 'next/link';

interface BreadcrumbItem {
  label: string;
  href: string;
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) return null;

  return (
    <nav className="text-sm mb-4" aria-label="Breadcrumb">
      <ol className="flex items-center gap-2 text-gray-500">
        {items.map((item, i) => (
          <li key={item.href} className="flex items-center gap-2">
            {i > 0 && <span>›</span>}
            {i === items.length - 1 ? (
              <span className="text-gray-900 font-medium">{item.label}</span>
            ) : (
              <Link
                href={item.href}
                className="hover:text-blue-600 hover:underline"
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

// Helper for common paths
export function getBreadcrumbsFromPath(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return [];

  const items: BreadcrumbItem[] = [{ label: 'Home', href: '/' }];
  let path = '';
  for (const seg of segments) {
    path += '/' + seg;
    items.push({
      label: seg.replace(/-/g, ' ').replace(/^\w/, (c) => c.toUpperCase()),
      href: path,
    });
  }
  return items;
}
```

---

## Bước 6: TopBar

**File:** `apps/web/components/layout/topbar.tsx`

```typescript
import Link from 'next/link';
import { CreditsBadge } from '@/components/credits-badge';
import { UserMenu } from './user-menu';
import { MobileMenu } from './mobile-menu';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

interface User {
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  tier: string;
  credits: number;
}

async function getCurrentUser(): Promise<User | null> {
  const token = await getAccessToken();
  if (!token) return null;

  try {
    const res = await apiFetch('/api/users/me', {}, token);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function TopBar() {
  const user = await getCurrentUser();

  return (
    <header className="sticky top-0 z-40 bg-white border-b">
      <div className="px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <MobileMenu />
          <Link href="/" className="font-bold text-xl text-blue-600">
            AppDK
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {user && <CreditsBadge />}
          {user ? (
            <UserMenu user={user} />
          ) : (
            <Link
              href="/login"
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
```

---

## Bước 7: Authenticated Layout

**File:** `apps/web/components/layout/authenticated-layout.tsx`

```typescript
import { redirect } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Sidebar } from './sidebar';
import { Breadcrumbs, getBreadcrumbsFromPath } from './breadcrumbs';
import { headers } from 'next/headers';

export async function AuthenticatedLayout({
  children,
  showBreadcrumbs = true,
}: {
  children: React.ReactNode;
  showBreadcrumbs?: boolean;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  // Get current pathname from headers (set by middleware in production)
  // For now, breadcrumbs are computed client-side
  const breadcrumbs: { label: string; href: string }[] = [];

  return (
    <div className="flex flex-1">
      <aside className="hidden lg:block w-64 border-r bg-white sticky top-16 h-[calc(100vh-4rem)]">
        <Sidebar />
      </aside>

      <main className="flex-1 p-4 lg:p-8 overflow-x-hidden">
        {showBreadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumbs items={breadcrumbs} />
        )}
        {children}
      </main>
    </div>
  );
}
```

---

## Bước 8: Dashboard Group Layout

**File:** `apps/web/app/(dashboard)/layout.tsx`

```typescript
import { TopBar } from '@/components/layout/topbar';
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout';

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <TopBar />
      <AuthenticatedLayout>{children}</AuthenticatedLayout>
    </div>
  );
}
```

---

## Bước 9: Root Layout Update

**File:** `apps/web/app/layout.tsx`

```typescript
import './globals.css';

export const metadata = {
  title: 'AppDK',
  description: 'AI YouTube Script Generator',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="bg-gray-50 min-h-screen">{children}</body>
    </html>
  );
}
```

> **Lưu ý:** Root layout giờ đơn giản (chỉ HTML/body). TopBar được đặt trong `(dashboard)/layout.tsx`. Public pages (`/`, `/login`, `/pricing`) tự handle TopBar hoặc không cần.

### Update cho Public Pages

**File:** `apps/web/app/(auth)/login/page.tsx` (wrap với TopBar)

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  // ... existing logic
  
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white">
        <div className="container mx-auto px-8 py-4">
          <Link href="/" className="font-bold text-xl text-blue-600">
            AppDK
          </Link>
        </div>
      </header>
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        {/* existing form */}
      </main>
    </div>
  );
}
```

---

## Bước 10: Verify

```bash
cd apps/web
pnpm dev
# Desktop: http://localhost:3000/dashboard
# Mobile: Resize browser < 1024px
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task11-navigation.md
cat docs/plan/SKILL-ROUTING-sprint4-task11-navigation.md
cat docs/plan/PLAN-sprint4-task11-navigation.md
cat docs/plan/MSEW-sprint4-task11-navigation.md
cat docs/plan/ACCEPTANCE-sprint4-task11-navigation.md
```