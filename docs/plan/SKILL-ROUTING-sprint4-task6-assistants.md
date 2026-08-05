# Sprint 4+ Task Group 6: Channel Assistants - Skill Routing

## Commands ĐƯỢC PHÉP

### File Operations
- ✅ Read, Write, StrReplace (chỉ trong apps/web)
- ✅ ReadLints, self-fix

### API Routes
- ✅ Create route handlers trong apps/web/app/api/assistants/
- ✅ Forward JWT to FastAPI

---

## Commands KHÔNG ĐƯỢC PHÉP

- ❌ Đổi Backend (apps/api, apps/worker)
- ❌ Đổi existing tables / migrations
- ❌ Launch subagents

---

## Patterns BẮT BUỘC

### 1. Server Component với Auth Check

```typescript
import { redirect } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';

export default async function Page() {
  const token = await getAccessToken();
  if (!token) redirect('/login');
  // ... fetch data
}
```

### 2. API Proxy với JWT

```typescript
import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET() {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const response = await apiFetch('/api/assistants', {}, token);
  const data = await response.json();
  return NextResponse.json(data);
}
```

### 3. Server Component Data Fetch

```typescript
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

async function getAssistants(token: string) {
  const res = await apiFetch('/api/assistants', {}, token);
  if (!res.ok) return [];
  return res.json();
}
```

---

## Files CÓ THỂ TẠO

- ✅ `apps/web/app/assistants/page.tsx`
- ✅ `apps/web/app/assistants/[id]/page.tsx`
- ✅ `apps/web/app/api/assistants/route.ts`
- ✅ `apps/web/app/api/assistants/[id]/route.ts`
- ✅ `apps/web/components/assistant-card.tsx`
- ✅ `apps/web/components/assistant-actions.tsx`

## Files KHÔNG ĐƯỢC SỬA

- ❌ `apps/api/modules/module_2a/*` (Backend)
- ❌ `apps/worker/*` (Celery)
- ❌ `supabase/migrations/*` (RLS đã có)
- ❌ `apps/web/lib/auth.ts`, `api-client.ts` (Task 2)
- ❌ `apps/web/components/job-card.tsx`, `sub-progress-list.tsx` (Task 4)