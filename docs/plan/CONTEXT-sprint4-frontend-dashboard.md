# Sprint 4 Task Group 4: Frontend Dashboard & Realtime

## 1. Context & Mục đích

### Bối cảnh

Sprint 4.4 xây **Frontend Dashboard** với:
- Input URL YouTube channel
- Sub-progress tracking (14 outputs)
- Realtime updates via Supabase Realtime
- Script Editor UI

### Phụ thuộc

- ✅ Task 1: User/RLS
- ✅ Task 2: Next.js BFF
- ✅ Task 3: Credit System
- ✅ Sprint 3: Script Generation Script

---

## 2. UI Pages

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/dashboard` | Overview + recent jobs |
| New Project | `/projects/new` | Input URL → start job |
| Job Progress | `/jobs/[id]` | Real-time progress |
| Script Editor | `/scripts/[id]` | Edit script, B-roll |

---

## 3. Realtime Channels

```typescript
// Subscribe to jobs table
supabase.channel('jobs').on('postgres_changes', {...}).subscribe();
```

## 4. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/dashboard/page.tsx` | Dashboard |
| `apps/web/app/projects/new/page.tsx` | New project form |
| `apps/web/app/jobs/[id]/page.tsx` | Job progress |
| `apps/web/app/scripts/[id]/page.tsx` | Script editor |
| `apps/web/components/progress-bar.tsx` | Sub-progress UI |
| `apps/web/components/script-editor.tsx` | Editor |
| `apps/web/lib/realtime.ts` | Supabase realtime client |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Dashboard shows user info |
| AC2 | New project form works |
| AC3 | Realtime progress updates |
| AC4 | Script editor saves |
| AC5 | Responsive UI |
