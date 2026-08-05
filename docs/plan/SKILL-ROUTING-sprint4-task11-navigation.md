# Sprint 4+ Task Group 11: Navigation - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (apps/web only)
- ✅ ReadLints

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Backend
- ❌ Đổi existing pages (chỉ wrap với layout)
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Sidebar Nav Item

```typescript
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

export function NavItem({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
  
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
        isActive
          ? 'bg-blue-50 text-blue-700 font-medium'
          : 'text-gray-700 hover:bg-gray-100'
      }`}
    >
      <span>{item.icon}</span>
      <span>{item.label}</span>
    </Link>
  );
}
```

### 2. Authenticated Layout Wrapper

```typescript
import { redirect } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Sidebar } from '@/components/layout/sidebar';
import { TopBar } from '@/components/layout/topbar';

export async function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  return (
    <div className="min-h-screen flex flex-col">
      <TopBar />
      <div className="flex flex-1">
        <aside className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </aside>
        <main className="flex-1 p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
```

### 3. Dropdown Pattern

```typescript
'use client';
import { useState, useRef, useEffect } from 'react';

export function UserMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)}>Avatar</button>
      {open && <div className="absolute right-0 top-12 ...">...</div>}
    </div>
  );
}
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/components/layout/sidebar.tsx`
- ✅ `apps/web/components/layout/topbar.tsx`
- ✅ `apps/web/components/layout/user-menu.tsx`
- ✅ `apps/web/components/layout/breadcrumbs.tsx`
- ✅ `apps/web/components/layout/mobile-menu.tsx`
- ✅ `apps/web/components/layout/authenticated-layout.tsx`
- ✅ `apps/web/lib/navigation.ts`

## Files CÓ THỂ SỬA
- ✅ `apps/web/app/layout.tsx` (restructure)
- ✅ `apps/web/app/(dashboard)/layout.tsx` (NEW - apply to dashboard pages)

## Files KHÔNG ĐƯỢC SỬA
- ❌ All Tasks 1-10 files (logic pages)
- ❌ Backend files