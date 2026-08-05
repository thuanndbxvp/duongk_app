# Sprint 4 Task Group 2: Next.js BFF - Skill Routing

## Commands ĐƯỢC PHÉP

### File Operations
- ✅ Read, Write, StrReplace (cho Next.js files)
- ✅ Shell: `pnpm init`, `pnpm add`, `pnpm dev`
- ✅ ReadLints

### Dependencies
- ✅ Install via pnpm (managed monorepo)
- ✅ thêm tới `apps/web/package.json`

---

## Commands KHÔNG ĐƯỢC PHÉP

- ❌ Đổi existing FastAPI code
- ❌ Đổi RLS policies (Task 1)
- ❌ Đổi Sprint 1-3 files
- ❌ Launch subagents

---

## Skills BẮT BUỘC

### 1. Next.js 15 App Router

```typescript
// app/api/auth/login/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
    const body = await req.json();
    // ... proxy to FastAPI
    return NextResponse.json(data);
}
```

### 2. Cookie Pattern

```typescript
import { cookies } from 'next/headers';

cookies().set({
    name: 'sb-access-token',
    value: token,
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60, // 1 hour
    path: '/',
});
```

### 3. Supabase Client (Server)

```typescript
import { createServerClient } from '@supabase/ssr';

const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { /* ... */ } }
);
```

---

## File Paths KHÔNG ĐƯỢC SỬA

- ❌ `apps/api/*` (FastAPI)
- ❌ `apps/worker/*` (Celery)
- ❌ `supabase/migrations/*` (Task 1)
- ❌ `package.json` (root - chỉ thêm workspace)

---

## Files CÓ THỂ TẠO

- ✅ `apps/web/package.json`
- ✅ `apps/web/next.config.js`
- ✅ `apps/web/tsconfig.json`
- ✅ `apps/web/tailwind.config.ts`
- ✅ `apps/web/app/layout.tsx`
- ✅ `apps/web/app/page.tsx`
- ✅ `apps/web/app/api/**/route.ts`
- ✅ `apps/web/lib/*.ts`
- ✅ `apps/web/components/*.tsx`

---

## Dependencies Cần Cài

```bash
cd apps/web
pnpm add next@15 react@19 react-dom@19
pnpm add @supabase/ssr @supabase/supabase-js
pnpm add -D typescript @types/react @types/node
pnpm add -D tailwindcss postcss autoprefixer
pnpm add -D eslint eslint-config-next
```
