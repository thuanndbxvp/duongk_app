# Sprint 4 Task Group 2: Next.js BFF - Acceptance Criteria

## Definition of Done

---

## AC1: Project Setup

- [ ] **AC1.1:** `apps/web/package.json` created
- [ ] **AC1.2:** Dependencies installed via `pnpm install`
- [ ] **AC1.3:** `next.config.js` configured
- [ ] **AC1.4:** `tsconfig.json` configured (strict mode)
- [ ] **AC1.5:** Tailwind set up with `globals.css`

### Test AC1:

```bash
cd apps/web && pnpm dev
# Should start on http://localhost:3000
```

---

## AC2: Auth Lib

- [ ] **AC2.1:** `lib/auth.ts` has `getAccessToken`, `getUser`, `setAuthCookies`, `clearAuthCookies`
- [ ] **AC2.2:** Cookies set as HttpOnly, Secure, SameSite=Lax
- [ ] **AC2.3:** Access token decoded correctly

### Test AC2:

```typescript
// Test cookie is HttpOnly
const cookie = cookies().get('sb-access-token');
expect(cookie?.httpOnly).toBe(true);
```

---

## AC3: API Client

- [ ] **AC3.1:** `lib/api-client.ts` exports `apiFetch`
- [ ] **AC3.2:** Auto-injects Authorization header
- [ ] **AC3.3:** Base URL from env

### Test AC3:

```typescript
const response = await apiFetch('/api/users/me', {}, 'fake-token');
expect(response.url).toContain(FASTAPI_URL);
```

---

## AC4: Auth Routes

- [ ] **AC4.1:** `POST /api/auth/login` calls Supabase Auth
- [ ] **AC4.2:** Sets cookies on success
- [ ] **AC4.3:** Returns 401 on bad credentials
- [ ] **AC4.4:** `POST /api/auth/logout` clears cookies

### Test AC4:

```bash
# Test login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
# Expect: 200 + Set-Cookie headers

# Test logout
curl -X POST http://localhost:3000/api/auth/logout
# Expect: 200 + cookies cleared
```

---

## AC5: API Proxy Routes

- [ ] **AC5.1:** `POST /api/scripts/generate` proxies to FastAPI
- [ ] **AC5.2:** `GET /api/jobs/[id]` proxies to FastAPI
- [ ] **AC5.3:** JWT injected from cookies
- [ ] **AC5.4:** Returns 401 if no JWT

### Test AC5:

```typescript
// Test missing token
const response = await fetch('http://localhost:3000/api/scripts/generate', {
  method: 'POST',
});
expect(response.status).toBe(401);
```

---

## AC6: UI Pages

- [ ] **AC6.1:** Landing page renders at `/`
- [ ] **AC6.2:** Login page renders at `/login`
- [ ] **AC6.3:** Login form submits to `/api/auth/login`
- [ ] **AC6.4:** Successful login redirects to `/dashboard`

---

## AC7: Code Quality

- [ ] **AC7.1:** TypeScript strict mode (no `any`)
- [ ] **AC7.2:** No `console.log` in production
- [ ] **AC7.3:** `pnpm lint` passes
- [ ] **AC7.4:** `pnpm type-check` passes

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] `pnpm dev` starts successfully
3. [ ] Login flow works end-to-end
4. [ ] API proxy works with cookies

---

## Sign-off

```
✓ Task: Sprint 4 - Next.js BFF
✓ Status: COMPLETED
✓ Files Created:
  - apps/web/package.json
  - apps/web/next.config.js
  - apps/web/tsconfig.json
  - apps/web/tailwind.config.ts
  - apps/web/lib/auth.ts
  - apps/web/lib/api-client.ts
  - apps/web/app/api/auth/login/route.ts
  - apps/web/app/api/auth/logout/route.ts
  - apps/web/app/api/scripts/generate/route.ts
  - apps/web/app/api/jobs/[id]/route.ts
  - apps/web/app/layout.tsx
  - apps/web/app/page.tsx
  - apps/web/app/(auth)/login/page.tsx
  - apps/web/app/globals.css
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Credit System
```
