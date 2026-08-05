# Sprint 4 Task Group 2: Next.js BFF - Plan

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  NEXT.JS BFF ARCHITECTURE                                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────┐      ┌──────────────────┐      ┌──────────────┐  │
│  │  Browser   │      │   Next.js BFF    │      │   FastAPI    │  │
│  │  (React)   │      │  (App Router)    │      │  (REST)      │  │
│  │            │      │                  │      │              │  │
│  │  Cookies   │◀────▶│  Route Handlers  │─────▶│  JWT Auth    │  │
│  │  (HttpOnly)│      │  (proxy + JWT)   │      │  (PyJWT)     │  │
│  └────────────┘      └──────────────────┘      └──────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Auth Flow

```
1. User clicks "Login" → POST /api/auth/login
   ↓
2. Next.js calls FastAPI: POST /api/auth/login (Email/Password)
   ↓
3. FastAPI returns tokens (access_token, refresh_token)
   ↓
4. Next.js set cookies (HttpOnly, Secure)
   ↓
5. Next.js redirects to /dashboard
```

## API Proxy Flow

```
1. Frontend: fetch('/api/scripts/generate', {body})
   ↓
2. Next.js Route Handler: 
   - Get JWT from cookies
   - Forward to FastAPI with Authorization header
   ↓
3. FastAPI: verify JWT, execute
   ↓
4. Return response to frontend
```

## Files to Create

### 1. Package & Config

- `apps/web/package.json` - Dependencies
- `apps/web/next.config.js` - Next.js config
- `apps/web/tsconfig.json` - TypeScript
- `apps/web/tailwind.config.ts` - Tailwind
- `apps/web/postcss.config.js`
- `apps/web/.env.local.example`

### 2. App Routes

- `apps/web/app/layout.tsx` - Root layout
- `apps/web/app/page.tsx` - Landing page
- `apps/web/app/(auth)/login/page.tsx` - Login form
- `apps/web/app/(auth)/signup/page.tsx` - Signup form
- `apps/web/app/api/auth/login/route.ts` - Login proxy
- `apps/web/app/api/auth/logout/route.ts` - Logout
- `apps/web/app/api/scripts/generate/route.ts` - Script proxy
- `apps/web/app/api/jobs/[id]/route.ts` - Job status

### 3. Lib

- `apps/web/lib/auth.ts` - Auth helpers
- `apps/web/lib/api-client.ts` - FastAPI client
- `apps/web/lib/supabase-client.ts` - Supabase client

### 4. Components

- `apps/web/components/auth-form.tsx` - Login form
- `apps/web/components/loading-spinner.tsx`

---

## Security

### Cookie Settings

```typescript
{
    httpOnly: true,             // JS cannot access
    secure: NODE_ENV === 'production',
    sameSite: 'lax',            // CSRF protection
    path: '/',
    maxAge: 60 * 60,           // 1 hour
}
```

### Token Storage

- Access token: HttpOnly cookie (NOT localStorage)
- Refresh token: HttpOnly cookie
- Frontend KHÔNG trực tiếp access tokens

### Defense in Depth

- Layer 1: Supabase Auth (signs JWT)
- Layer 2: FastAPI verifies JWT signature (PyJWT)
- Layer 3: RLS enforces data ownership (Postgres)
