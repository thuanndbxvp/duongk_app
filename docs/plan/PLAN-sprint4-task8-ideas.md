# Sprint 4+ Task Group 8: Idea Generation - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  IDEA GENERATION FLOW                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → /ideas/[assistant_id]                                    │
│     │                                                            │
│     ▼                                                            │
│  BFF GET /api/ideas/[assistant_id]                              │
│     │                                                            │
│     ▼                                                            │
│  Backend: Query generated_ideas WHERE assistant_id              │
│     │                                                            │
│     ▼                                                            │
│  UI: List cards sorted by gap_score                             │
│     │                                                            │
│     ├── Filter (confidence: high/medium/low)                    │
│     ├── Search (by topic)                                        │
│     └── Click "Tạo Script" → POST /api/scripts/generate        │
│                                                                   │
│  "Regenerate" button:                                            │
│     │                                                            │
│     ▼                                                            │
│  POST /api/jobs/trigger task_type=idea_generation               │
│     │                                                            │
│     ▼                                                            │
│  Redirect to /jobs/[job_id]                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Files to Create

### 1. Page

- `apps/web/app/ideas/[assistant_id]/page.tsx` - Server Component

### 2. API Proxy

- `apps/web/app/api/ideas/[assistant_id]/route.ts` - GET list

### 3. Components

- `apps/web/components/ideas/idea-card.tsx` - Card with topic + gap score
- `apps/web/components/ideas/idea-filters.tsx` - Filter UI (client)
- `apps/web/components/ideas/regenerate-button.tsx` - Trigger regen
- `apps/web/components/ideas/ideas-list.tsx` - Client wrapper with state

---

## Constraints

1. **Server fetch** initial ideas
2. **Client filter/sort** without refetch
3. **Trigger script** with selected idea topic
4. **Confirm before charge** when regenerating
5. **Empty state** for no ideas