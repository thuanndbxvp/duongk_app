# Sprint 4+ Task Group 7: Deep Analysis - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (chỉ apps/web)
- ✅ ReadLints

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Backend modules
- ❌ Đổi Tasks 1-6 code
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Client-Side Tabs

```typescript
'use client';
import { useState } from 'react';

const TABS = ['overview', 'deterministic', 'nlp', 'llm', 'insights', 'thumbnail'];

export function AnalysisTabs({ data }: { data: any }) {
  const [tab, setTab] = useState('overview');
  return (
    <>
      <div className="flex border-b">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mt-6">
        {tab === 'overview' && <Overview data={data} />}
        {tab === 'deterministic' && <Deterministic outputs={data.outputs} />}
        {/* ... */}
      </div>
    </>
  );
}
```

### 2. Reusable Output Card

```typescript
export function OutputCard({
  number,
  title,
  description,
  data,
  cost,
}: OutputCardProps) {
  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs font-semibold bg-blue-100 text-blue-800 px-2 py-1 rounded">
            Output #{number}
          </span>
          <h3 className="text-lg font-bold mt-2">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        {cost > 0 && (
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            ${cost.toFixed(3)}
          </span>
        )}
      </div>
      <div className="mt-4">
        <JsonViewer data={data} />
      </div>
    </div>
  );
}
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/app/analysis/[assistant_id]/page.tsx`
- ✅ `apps/web/app/api/analysis/[assistant_id]/route.ts`
- ✅ `apps/web/components/analysis/*` (10 components)

## Files KHÔNG ĐƯỢC SỬA
- ❌ `apps/api/modules/analysis/*`
- ❌ `apps/worker/tasks/analysis_task.py`
- ❌ `apps/web/components/assistant-*` (Task 6)