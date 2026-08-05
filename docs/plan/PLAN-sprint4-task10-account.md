# Sprint 4+ Task Group 10: Account Settings - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  ACCOUNT SETTINGS FLOW                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → /account/settings                                        │
│     │                                                            │
│     ▼                                                            │
│  Server fetch /api/users/me                                      │
│     │                                                            │
│     ▼                                                            │
│  Show Profile / Password / Danger Zone                           │
│                                                                   │
│  Profile update:                                                 │
│     │                                                            │
│     ▼                                                            │
│  PATCH /api/users/me (FastAPI đã có)                            │
│                                                                   │
│  Password change:                                                │
│     │                                                            │
│     ▼                                                            │
│  Supabase Auth API (POST /auth/v1/user)                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Files to Create

### 1. Account Settings

- `apps/web/app/account/settings/page.tsx`
- `apps/web/components/profile-form.tsx`
- `apps/web/components/password-form.tsx`

### 2. Pricing

- `apps/web/app/pricing/page.tsx`
- `apps/web/components/pricing-card.tsx`

### 3. API Routes

- `apps/web/app/api/account/update-profile/route.ts`
- `apps/web/app/api/account/change-password/route.ts`

---

## Backend Reference

### Existing endpoints

```python
PATCH /api/users/me  # Update full_name + avatar_url (đã có)
```

### Supabase Auth

```typescript
POST {SUPABASE_URL}/auth/v1/user
Headers: Authorization: Bearer <access_token>
Body: { password: "new-password" }
```

---

## Constraints

1. **Email readonly** (Supabase Auth limitation)
2. **Password min 8 chars**
3. **Delete account requires confirm dialog**
4. **Tier upgrade is mock** (no payment integration yet)
5. **RLS isolation**