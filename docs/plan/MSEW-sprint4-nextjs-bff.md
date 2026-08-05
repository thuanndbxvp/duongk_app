# Sprint 4 Task Group 2: Next.js BFF - MSEW

## Checklist

- [ ] Bước 1: Init Next.js project
- [ ] Bước 2: Setup package.json
- [ ] Bước 3: Configure Next.js + TypeScript + Tailwind
- [ ] Bước 4: Create lib/ (auth, api-client)
- [ ] Bước 5: Create auth routes (login, logout)
- [ ] Bước 6: Create API proxy routes
- [ ] Bước 7: Create UI pages
- [ ] Bước 8: Verify

---

## Bước 1: Init Project

```bash
mkdir apps/web
cd apps/web
pnpm init
```

---

## Bước 2: package.json

**File:** `apps/web/package.json`

```json
{
  "name": "@appdk/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "@supabase/ssr": "^0.5.0",
    "@supabase/supabase-js": "^2.45.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "15.0.0"
  }
}
```

---

## Bước 3: Configuration Files

### `apps/web/next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: `${process.env.FASTAPI_URL}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
```

### `apps/web/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### `apps/web/tailwind.config.ts`

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

### `apps/web/.env.local.example`

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# FastAPI
FASTAPI_URL=http://localhost:8000
```

---

## Bước 4: Lib Files

### `apps/web/lib/auth.ts`

```typescript
/**
 * Auth helpers for Next.js BFF.
 */
import { cookies } from 'next/headers';
import { jwtDecode } from 'jwt-decode';

const ACCESS_TOKEN_COOKIE = 'sb-access-token';
const REFRESH_TOKEN_COOKIE = 'sb-refresh-token';

export interface User {
  sub: string;
  email: string;
  exp: number;
}

export function getAccessToken(): string | null {
  return cookies().get(ACCESS_TOKEN_COOKIE)?.value ?? null;
}

export function getRefreshToken(): string | null {
  return cookies().get(REFRESH_TOKEN_COOKIE)?.value ?? null;
}

export function getUser(): User | null {
  const token = getAccessToken();
  if (!token) return null;
  
  try {
    return jwtDecode<User>(token);
  } catch {
    return null;
  }
}

export function setAuthCookies(accessToken: string, refreshToken: string) {
  const cookieOpts = {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
    maxAge: 60 * 60, // 1 hour
  };

  cookies().set(ACCESS_TOKEN_COOKIE, accessToken, cookieOpts);
  cookies().set(REFRESH_TOKEN_COOKIE, refreshToken, cookieOpts);
}

export function clearAuthCookies() {
  cookies().delete(ACCESS_TOKEN_COOKIE);
  cookies().delete(REFRESH_TOKEN_COOKIE);
}
```

### `apps/web/lib/api-client.ts`

```typescript
/**
 * FastAPI client with automatic JWT injection.
 */
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  accessToken?: string
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  return fetch(`${FASTAPI_URL}${path}`, {
    ...options,
    headers,
  });
}
```

---

## Bước 5: Auth Routes

### `apps/web/app/api/auth/login/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { setAuthCookies } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const body = await req.json();

  // Call Supabase Auth API
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/token?grant_type=password`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      },
      body: JSON.stringify({
        email: body.email,
        password: body.password,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    return NextResponse.json(
      { error: error.error_description || 'Login failed' },
      { status: response.status }
    );
  }

  const data = await response.json();

  // Set HttpOnly cookies
  setAuthCookies(data.access_token, data.refresh_token);

  return NextResponse.json({
    user: data.user,
    redirect: '/dashboard',
  });
}
```

### `apps/web/app/api/auth/logout/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { clearAuthCookies } from '@/lib/auth';

export async function POST() {
  clearAuthCookies();
  return NextResponse.json({ success: true });
}
```

---

## Bước 6: API Proxy Routes

### `apps/web/app/api/scripts/generate/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const token = getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json();

  const response = await apiFetch(
    '/api/scripts/generate',
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
    token
  );

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

### `apps/web/app/api/jobs/[id]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const token = getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const response = await apiFetch(
    `/api/jobs/${params.id}`,
    {},
    token
  );

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

---

## Bước 7: UI Pages

### `apps/web/app/layout.tsx`

```typescript
import './globals.css';

export const metadata = {
  title: 'AppDK',
  description: 'AI YouTube Script Generator',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
```

### `apps/web/app/page.tsx`

```typescript
export default function HomePage() {
  return (
    <main className="container mx-auto p-8">
      <h1 className="text-4xl font-bold">AppDK</h1>
      <p className="text-gray-600 mt-4">
        AI YouTube Script Generator - Tạo kịch bản YouTube chuẩn phong cách kênh mẫu
      </p>
      <a href="/login" className="text-blue-600 mt-4 inline-block">
        Đăng nhập →
      </a>
    </main>
  );
}
```

### `apps/web/app/(auth)/login/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
      const data = await response.json();
      router.push(data.redirect || '/dashboard');
    } else {
      const error = await response.json();
      setError(error.error || 'Login failed');
    }
    setLoading(false);
  }

  return (
    <main className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-96 space-y-4">
        <h1 className="text-2xl font-bold">Đăng nhập</h1>
        {error && <p className="text-red-600">{error}</p>}
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          required
          className="w-full p-2 border rounded"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Mật khẩu"
          required
          className="w-full p-2 border rounded"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full p-2 bg-blue-600 text-white rounded"
        >
          {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>
    </main>
  );
}
```

### `apps/web/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Bước 8: Verify

```bash
cd apps/web
pnpm install
pnpm dev
# Mở http://localhost:3000
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-nextjs-bff.md
cat docs/plan/SKILL-ROUTING-sprint4-nextjs-bff.md
cat docs/plan/PLAN-sprint4-nextjs-bff.md
cat docs/plan/MSEW-sprint4-nextjs-bff.md
cat docs/plan/ACCEPTANCE-sprint4-nextjs-bff.md
```
