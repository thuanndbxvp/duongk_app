# Sprint 4+ Task Group 10: Account Settings - Acceptance Criteria

## Definition of Done

---

## AC1: Settings Page

- [ ] **AC1.1:** `/account/settings` renders
- [ ] **AC1.2:** Shows email (readonly)
- [ ] **AC1.3:** Shows full_name + avatar_url fields
- [ ] **AC1.4:** Profile save works
- [ ] **AC1.5:** Password change form validates
- [ ] **AC1.6:** Password min 8 chars enforced
- [ ] **AC1.7:** Confirm password match
- [ ] **AC1.8:** Danger zone with confirm dialog

---

## AC2: Profile Update API

- [ ] **AC2.1:** `PATCH /api/account/update-profile` proxies to FastAPI
- [ ] **AC2.2:** JWT enforced
- [ ] **AC2.3:** Returns 200 on success
- [ ] **AC2.4:** Returns 400 on empty update

---

## AC3: Change Password API

- [ ] **AC3.1:** `POST /api/account/change-password` works
- [ ] **AC3.2:** Validates password length
- [ ] **AC3.3:** Validates confirmation match
- [ ] **AC3.4:** Calls Supabase Auth API
- [ ] **AC3.5:** JWT enforced

---

## AC4: Pricing Page

- [ ] **AC4.1:** `/pricing` renders
- [ ] **AC4.2:** Shows 3 tiers (Free/Pro/Enterprise)
- [ ] **AC4.3:** Current tier highlighted
- [ ] **AC4.4:** "Popular" badge on Pro
- [ ] **AC4.5:** Upgrade button (mock)
- [ ] **AC4.6:** Enterprise links to email

---

## AC5: PricingCard

- [ ] **AC5.1:** Shows tier name + price
- [ ] **AC5.2:** Lists features
- [ ] **AC5.3:** Different styles per tier
- [ ] **AC5.4:** Current plan disabled

---

## AC6: RLS

- [ ] **AC6.1:** User A cannot update user B's profile
- [ ] **AC6.2:** User A cannot change user B's password

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] Forms validate properly
3. [ ] Pricing page renders

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 10 - Account Settings
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/app/account/settings/page.tsx
  - apps/web/app/pricing/page.tsx
  - apps/web/app/api/account/update-profile/route.ts
  - apps/web/app/api/account/change-password/route.ts
  - apps/web/components/profile-form.tsx
  - apps/web/components/password-form.tsx
  - apps/web/components/pricing-card.tsx
✓ All Acceptance Criteria: PASSED
✓ SPRINT 4+ COMPLETE
```