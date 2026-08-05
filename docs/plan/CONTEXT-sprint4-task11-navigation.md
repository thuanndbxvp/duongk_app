# Sprint 4+ Task Group 11: Navigation & Layout

## 1. Context & Mục đích

### Bối cảnh

Layout hiện tại (`apps/web/app/layout.tsx`) **chỉ có header cơ bản**:
- Logo + CreditsBadge
- **KHÔNG CÓ** navigation menu
- **KHÔNG CÓ** sidebar
- **KHÔNG CÓ** user menu / dropdown
- **KHÔNG CÓ** breadcrumbs
- **KHÔNG CÓ** mobile menu

User phải **nhớ URL** hoặc **back button** để điều hướng. Trải nghiệm rất tệ.

### Mục đích task group này

- **Top Navigation Bar** với menu items
- **Sidebar** cho authenticated pages (collapsible)
- **User Avatar Dropdown** (profile, billing, logout)
- **Breadcrumbs** cho nested pages
- **Mobile responsive** với hamburger menu

### Phụ thuộc

- ✅ Task 1-10 đã xong
- ✅ Auth user info từ `/api/users/me`

---

## 2. UI Layout Design

### Desktop Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ TopBar: [Logo] ........... [Credits] [Avatar▼]                       │
├─────────────┬────────────────────────────────────────────────────────┤
│             │                                                         │
│  Sidebar    │  Main Content Area                                     │
│             │                                                         │
│ 📊 Dashboard│  ┌─────────────────────────────────────────┐          │
│ 📺 Channels │  │ Breadcrumbs: Home > Channels > Detail  │          │
│ 🧠 Analysis │  ├─────────────────────────────────────────┤          │
│ 💡 Ideas    │  │                                          │          │
│ ✍️ Scripts │  │   [Page content here]                   │          │
│ 💰 Billing  │  │                                          │          │
│ 👤 Account  │  │                                          │          │
│ 📈 Pricing  │  │                                          │          │
│             │  │                                          │          │
│ ──────────  │  └─────────────────────────────────────────┘          │
│ 🔓 Logout   │                                                         │
│             │                                                         │
└─────────────┴────────────────────────────────────────────────────────┘
```

### Mobile Layout

```
┌─────────────────────────────────────────────────────┐
│ [☰] AppDK              [Credits] [Avatar▼]          │
├─────────────────────────────────────────────────────┤
│ Hamburger Menu (slide-in):                          │
│  📊 Dashboard                                        │
│  📺 Channels                                         │
│  🧠 Analysis                                         │
│  💡 Ideas                                            │
│  ✍️ Scripts                                          │
│  💰 Billing                                          │
│  👤 Account                                          │
│  📈 Pricing                                          │
│  ──────────                                          │
│  🔓 Logout                                           │
├─────────────────────────────────────────────────────┤
│  [Page content here]                                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 3. Navigation Structure

### Public Routes (không cần auth)

| Path | Label | Icon |
|------|-------|------|
| `/` | Home | 🏠 |
| `/pricing` | Pricing | 📈 |
| `/login` | Login | 🔑 |
| `/register` | Sign up | ✨ |

### Authenticated Routes

| Path | Label | Icon | Tier Required |
|------|-------|------|---------------|
| `/dashboard` | Dashboard | 📊 | All |
| `/assistants` | Channel DNA | 📺 | All |
| `/assistants/[id]` | Chi tiết kênh | 📺 | All |
| `/analysis/[id]` | Deep Analysis | 🧠 | All |
| `/ideas/[id]` | Ideas | 💡 | All |
| `/scripts/[id]` | Script Editor | ✍️ | All |
| `/projects/new` | New Project | ➕ | All |
| `/jobs/[id]` | Job Progress | ⏱️ | All |
| `/billing` | Billing | 💰 | All |
| `/account/settings` | Account | 👤 | All |

### User Menu Dropdown

```
┌─────────────────────────┐
│ 👤 user@example.com     │
│ Tier: Pro • 87 credits │
├─────────────────────────┤
│ 👤 Account Settings     │
│ 💰 Billing              │
├─────────────────────────┤
│ 🔓 Logout               │
└─────────────────────────┘
```

---

## 4. Files to Create / Update

### New Files (7)

| File | Purpose |
|------|---------|
| `apps/web/components/layout/sidebar.tsx` | Left sidebar nav |
| `apps/web/components/layout/topbar.tsx` | Top bar |
| `apps/web/components/layout/user-menu.tsx` | Avatar dropdown |
| `apps/web/components/layout/breadcrumbs.tsx` | Breadcrumb component |
| `apps/web/components/layout/mobile-menu.tsx` | Hamburger menu |
| `apps/web/components/layout/authenticated-layout.tsx` | Wrapper layout |
| `apps/web/lib/navigation.ts` | Nav config |

### Updated Files (1)

| File | Changes |
|------|---------|
| `apps/web/app/layout.tsx` | Restructure to include nav |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Sidebar shows on desktop |
| AC2 | Hamburger menu on mobile |
| AC3 | Active route highlighted |
| AC4 | User menu dropdown works |
| AC5 | Breadcrumbs navigate correctly |
| AC6 | Logout works |
| AC7 | Responsive 320px-1920px |
| AC8 | Auth check (redirect if no session) |
| AC9 | SSR-friendly (no hydration errors) |
| AC10 | Keyboard accessible |