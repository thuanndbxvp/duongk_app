# Sprint 4+ Task Group 11: Navigation - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  LAYOUT ARCHITECTURE                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  app/                                                             │
│  ├── layout.tsx               ← Root (HTML + body)                │
│  │                                                                │
│  ├── (auth)/                  ← Group: NO sidebar (login/register)│
│  │   ├── login/page.tsx                                          │
│  │   └── register/page.tsx                                        │
│  │                                                                │
│  ├── (dashboard)/             ← Group: HAS sidebar                │
│  │   ├── layout.tsx           ← AuthenticatedLayout              │
│  │   ├── dashboard/page.tsx                                       │
│  │   ├── assistants/                                            │
│  │   ├── analysis/                                               │
│  │   ├── ideas/                                                  │
│  │   ├── scripts/                                                │
│  │   ├── jobs/                                                   │
│  │   ├── projects/                                               │
│  │   ├── billing/                                                │
│  │   └── account/                                                │
│  │                                                                │
│  └── pricing/page.tsx         ← Public, no auth needed            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Tree

```
<RootLayout>
  <html><body>
    <TopBar />                    ← Always visible (logo + user menu)
    <AuthenticatedLayout>         ← For dashboard pages only
      <Sidebar />                 ← Desktop: left nav
      <MobileMenu />              ← Mobile: hamburger
      <Breadcrumbs />             ← Page path
      {children}                  ← Page content
    </AuthenticatedLayout>
  </body></html>
</RootLayout>
```

## Active Route Highlighting

```typescript
const pathname = usePathname();
const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
```

## Mobile Responsiveness

- **< 1024px (lg):** Sidebar ẩn, hiện hamburger
- **≥ 1024px:** Sidebar hiện, hamburger ẩn

## Files to Create

### 1. lib/navigation.ts

```typescript
export const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/assistants', label: 'Channels', icon: '📺' },
  { href: '/projects/new', label: 'New Project', icon: '➕' },
  { href: '/billing', label: 'Billing', icon: '💰' },
  { href: '/account/settings', label: 'Account', icon: '👤' },
  { href: '/pricing', label: 'Pricing', icon: '📈' },
];
```

### 2. components/layout/sidebar.tsx

Desktop sidebar với NavItems.

### 3. components/layout/topbar.tsx

Top bar với logo + UserMenu + MobileMenu trigger.

### 4. components/layout/user-menu.tsx

Avatar dropdown với profile/logout.

### 5. components/layout/mobile-menu.tsx

Slide-in hamburger menu.

### 6. components/layout/breadcrumbs.tsx

Path-based breadcrumbs từ URL.

### 7. components/layout/authenticated-layout.tsx

Wrapper với auth check + Sidebar/Topbar.

### 8. app/(dashboard)/layout.tsx

Apply AuthenticatedLayout.

---

## Constraints

1. **Server Component auth check** ở AuthenticatedLayout
2. **Client Component** cho interactive (dropdown, hamburger)
3. **Hydration-safe** (không dùng localStorage ở SSR)
4. **Keyboard accessible** (Tab + Enter)
5. **Mobile-first responsive**