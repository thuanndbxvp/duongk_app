# Sprint 4 Task Group 4: Frontend Dashboard - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  DASHBOARD PAGES                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  /dashboard          → Overview + recent jobs                    │
│  /projects/new       → Input URL → start job                     │
│  /jobs/[id]          → Real-time progress (14 outputs)            │
│  /scripts/[id]       → Edit script + B-roll                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Realtime Pattern

```typescript
// subscribe to jobs table
const channel = supabase
  .channel(`job-${jobId}`)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'jobs',
    filter: `id=eq.${jobId}`,
  }, (payload) => {
    setJob(payload.new);
  })
  .subscribe();
```

## Files to Create

### 1. Dashboard

- `apps/web/app/dashboard/page.tsx` - Overview
- `apps/web/components/job-card.tsx` - Job display

### 2. New Project

- `apps/web/app/projects/new/page.tsx` - Form
- `apps/web/components/project-form.tsx` - Input

### 3. Job Progress

- `apps/web/app/jobs/[id]/page.tsx` - Detail
- `apps/web/components/progress-bar.tsx`
- `apps/web/components/sub-progress-list.tsx`

### 4. Script Editor

- `apps/web/app/scripts/[id]/page.tsx`
- `apps/web/components/script-editor.tsx`
- `apps/web/components/scene-timeline.tsx`

### 5. Realtime Client

- `apps/web/lib/realtime.ts`
