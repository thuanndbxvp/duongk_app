# Sprint 4 Task Group 4: Frontend Dashboard - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (chỉ trong apps/web)
- ✅ React 19 patterns
- ✅ shadcn/ui patterns

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Backend (apps/api, apps/worker)
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Server Components (App Router)

```typescript
// app/dashboard/page.tsx - Server Component mặc định
export default async function Page() {
  const data = await fetch(...);
  return <div>{data}</div>;
}
```

### 2. Client Components (when needed)

```typescript
'use client';
import { useState } from 'react';
```

### 3. Realtime Pattern

```typescript
import { createBrowserClient } from '@supabase/ssr';

useEffect(() => {
  const supabase = createBrowserClient(...);
  const channel = supabase.channel('jobs').on('postgres_changes', ...).subscribe();
  return () => { supabase.removeChannel(channel); };
}, []);
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/app/dashboard/page.tsx`
- ✅ `apps/web/app/projects/new/page.tsx`
- ✅ `apps/web/app/jobs/[id]/page.tsx`
- ✅ `apps/web/app/scripts/[id]/page.tsx`
- ✅ `apps/web/components/progress-bar.tsx`
- ✅ `apps/web/components/script-editor.tsx`
- ✅ `apps/web/lib/realtime.ts`

## Files KHÔNG ĐƯỢC SỬA
- ❌ `apps/api/*`
- ❌ `apps/worker/*`
- ❌ `apps/web/lib/auth.ts` (Task 2)
- ❌ `apps/web/app/api/*` (Task 2)
