# Sprint 4+ Task Group 10: Account Settings & Pricing

## 1. Context & Mục đích

### Bối cảnh

UI hiện tại **THIẾU** các trang nghiệp vụ cuối:
- User không thể edit profile
- User không thấy pricing tiers để upgrade
- User không thể change password
- User không thể delete account

### Mục đích task group này

- **`/account/settings`** - Quản lý profile + security
- **`/pricing`** - So sánh tiers (free/pro/enterprise)
- **Tier upgrade flow** (mock - no payment yet)

### Phụ thuộc

- ✅ Task 1: User & RLS
- ✅ Task 2: BFF
- ✅ Task 9: Billing (để hiển thị credit info)

---

## 2. UI Layout

### `/account/settings`

```
┌─────────────────────────────────────────────────────────────────────┐
│  Account Settings                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─ Profile ──────────────────────────────────────────┐            │
│  │  Email: user@example.com (cannot change)            │            │
│  │  Full Name: [input]                                  │            │
│  │  Avatar URL: [input]                                 │            │
│  │  [Save Changes]                                      │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  ┌─ Security ──────────────────────────────────────────┐            │
│  │  Change Password                                     │            │
│  │  Current: [input]                                    │            │
│  │  New: [input]                                        │            │
│  │  Confirm: [input]                                    │            │
│  │  [Update Password]                                   │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  ┌─ Danger Zone ──────────────────────────────────────┐            │
│  │  Delete Account (irreversible)                       │            │
│  │  [Delete Account]                                    │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### `/pricing`

```
┌─────────────────────────────────────────────────────────────────────┐
│  Choose Your Plan                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ FREE         │ │ PRO          │ │ ENTERPRISE   │                │
│  │ $0/mo        │ │ $19/mo       │ │ Custom       │                │
│  │              │ │ ⭐ POPULAR   │ │              │                │
│  │ • 100 credits│ │ • 500 credits│ │ • 5000 credits│                │
│  │ • Basic AI   │ │ • All AI     │ │ • All AI     │                │
│  │ • No support │ │ • Email sup. │ │ • Priority   │                │
│  │              │ │              │ │              │                │
│  │ [Current]    │ │ [Upgrade]    │ │ [Contact]    │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/account/settings/page.tsx` | Settings main page |
| `apps/web/app/pricing/page.tsx` | Pricing tiers |
| `apps/web/app/api/account/update-profile/route.ts` | Update profile API |
| `apps/web/app/api/account/change-password/route.ts` | Change pw API |
| `apps/web/components/profile-form.tsx` | Edit profile form |
| `apps/web/components/password-form.tsx` | Change pw form |
| `apps/web/components/pricing-card.tsx` | Tier card |

---

## 4. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | /account/settings renders |
| AC2 | Profile form saves |
| AC3 | Password form validates |
| AC4 | Delete account confirm |
| AC5 | /pricing shows 3 tiers |
| AC6 | Current tier highlighted |
| AC7 | Upgrade button (mock) |
| AC8 | RLS isolation |