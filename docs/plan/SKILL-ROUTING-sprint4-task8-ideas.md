# Sprint 4+ Task Group 8: Idea Generation - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (apps/web only)
- ✅ ReadLints

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Backend
- ❌ Đổi Tasks 6-7 code
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Server Component + Client Filter

```typescript
// page.tsx - Server
export default async function Page({ params }) {
  const ideas = await fetchIdeas();
  return <IdeasList ideas={ideas} />;  // Client component
}

// ideas-list.tsx - Client
'use client';
function IdeasList({ ideas }) {
  const [filter, setFilter] = useState('all');
  // ... filter logic
}
```

### 2. Gap Score Visualization

```typescript
function GapScoreBadge({ score }: { score: number }) {
  const color = score >= 70 ? 'bg-green-500' :
                score >= 40 ? 'bg-yellow-500' :
                              'bg-red-500';
  return (
    <span className={`${color} text-white px-2 py-1 rounded-full text-sm font-bold`}>
      {score}
    </span>
  );
}
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/app/ideas/[assistant_id]/page.tsx`
- ✅ `apps/web/app/api/ideas/[assistant_id]/route.ts`
- ✅ `apps/web/components/ideas/idea-card.tsx`
- ✅ `apps/web/components/ideas/idea-filters.tsx`
- ✅ `apps/web/components/ideas/regenerate-button.tsx`

## Files KHÔNG ĐƯỢC SỬA
- ❌ `apps/worker/tasks/idea_generate.py`
- ❌ `apps/web/components/assistant-*` (Task 6)
- ❌ `apps/web/components/analysis/*` (Task 7)