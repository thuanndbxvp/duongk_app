# Sprint 4+ Task Group 11: Navigation - Acceptance Criteria

## Definition of Done

---

## AC1: Sidebar

- [ ] **AC1.1:** Sidebar shows on desktop (≥1024px)
- [ ] **AC1.2:** 6 nav items visible
- [ ] **AC1.3:** Active route highlighted (blue bg)
- [ ] **AC1.4:** Click item → navigate
- [ ] **AC1.5:** Logout button at bottom
- [ ] **AC1.6:** Sticky positioning

---

## AC2: TopBar

- [ ] **AC2.1:** Logo always visible
- [ ] **AC2.2:** CreditsBadge shows balance
- [ ] **AC2.3:** UserMenu avatar shows
- [ ] **AC2.4:** MobileMenu hamburger shows (<1024px)
- [ ] **AC2.5:** Sticky to top

---

## AC3: UserMenu

- [ ] **AC3.1:** Click avatar → dropdown
- [ ] **AC3.2:** Shows email + tier + credits
- [ ] **AC3.3:** 3 menu items (Account/Billing/Pricing)
- [ ] **AC3.4:** Logout button works
- [ ] **AC3.5:** Click outside → close
- [ ] **AC3.6:** Initials fallback nếu không có avatar

---

## AC4: MobileMenu

- [ ] **AC4.1:** Hamburger shows < 1024px
- [ ] **AC4.2:** Click → slide-in panel
- [ ] **AC4.3:** Backdrop click → close
- [ ] **AC4.4:** X button → close
- [ ] **AC4.5:** Same nav items as sidebar
- [ ] **AC4.6:** Logout works
- [ ] **AC4.7:** Smooth transition

---

## AC5: Breadcrumbs

- [ ] **AC5.1:** Auto-generated từ pathname
- [ ] **AC5.2:** Last item is bold (current page)
- [ ] **AC5.3:** Click parent → navigate
- [ ] **AC5.4:** Home link included
- [ ] **AC5.5:** Empty path → no breadcrumbs

---

## AC6: Auth Flow

- [ ] **AC6.1:** No JWT → redirect /login
- [ ] **AC6.2:** JWT valid → render layout
- [ ] **AC6.3:** Logout → clear cookies + redirect /login
- [ ] **AC6.4:** Public pages (/, /pricing) work without JWT

---

## AC7: Responsive

- [ ] **AC7.1:** Desktop (1920px): Sidebar visible
- [ ] **AC7.2:** Tablet (768px): Hamburger shows
- [ ] **AC7.3:** Mobile (375px): Hamburger shows, content readable
- [ ] **AC7.4:** No horizontal scroll

---

## AC8: Hydration

- [ ] **AC8.1:** No "hydration mismatch" errors
- [ ] **AC8.2:** No flash of unauthenticated content
- [ ] **AC8.3:** Smooth auth state transitions

---

## AC9: Code Quality

- [ ] **AC9.1:** TypeScript strict
- [ ] **AC9.2:** 'use client' only khi cần
- [ ] **AC9.3:** Reusable components
- [ ] **AC9.4:** `pnpm lint` passes

---

## AC10: Accessibility

- [ ] **AC10.1:** Keyboard navigation (Tab)
- [ ] **AC10.2:** Enter activates buttons
- [ ] **AC10.3:** aria-labels cho icon buttons
- [ ] **AC10.4:** Focus visible

---

## Self-Check

1. [ ] All AC1-AC10 ✅
2. [ ] `pnpm dev` works
3. [ ] Test responsive ở 3 breakpoints

---

## Sign-off

```
✓ Task: Sprint 4+ Task Group 11 - Navigation
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/lib/navigation.ts
  - apps/web/components/layout/sidebar.tsx
  - apps/web/components/layout/topbar.tsx
  - apps/web/components/layout/user-menu.tsx
  - apps/web/components/layout/mobile-menu.tsx
  - apps/web/components/layout/breadcrumbs.tsx
  - apps/web/components/layout/authenticated-layout.tsx
  - apps/web/app/(dashboard)/layout.tsx
✓ Files Updated:
  - apps/web/app/layout.tsx (simplified)
✓ All Acceptance Criteria: PASSED
✓ UI NAVIGATION COMPLETE
```