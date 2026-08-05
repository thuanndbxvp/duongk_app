# Sprint 4+ Task Group 8: Idea Generation - MSEW

## Checklist

- [ ] Bước 1: API proxy
- [ ] Bước 2: IdeaCard component
- [ ] Bước 3: IdeaFilters component
- [ ] Bước 4: RegenerateButton
- [ ] Bước 5: IdeasList (client wrapper)
- [ ] Bước 6: Main page
- [ ] Bước 7: Verify

---

## Bước 1: API Proxy

**File:** `apps/web/app/api/ideas/[assistant_id]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ assistant_id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { assistant_id } = await params;

  try {
    const response = await apiFetch(
      `/api/ideas/${assistant_id}`,
      {},
      token
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

---

## Bước 2: IdeaCard Component

**File:** `apps/web/components/ideas/idea-card.tsx`

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export function IdeaCard({
  idea,
  assistantId,
}: {
  idea: Idea;
  assistantId: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const gapColor =
    idea.gap_score >= 70
      ? 'bg-green-500'
      : idea.gap_score >= 40
      ? 'bg-yellow-500'
      : 'bg-red-500';

  const confidenceColor = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  }[idea.confidence];

  async function generateScript() {
    setLoading(true);
    try {
      const response = await fetch('/api/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          topic: idea.idea_topic,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/jobs/${data.job_id}`);
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📌</span>
            <h3 className="text-xl font-bold">{idea.idea_topic}</h3>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`px-2 py-1 rounded-full font-bold text-white ${gapColor}`}>
              Gap: {idea.gap_score}
            </span>
            <span className={`px-2 py-1 rounded-full font-medium text-xs ${confidenceColor}`}>
              {idea.confidence.toUpperCase()}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
              Cluster {idea.cluster_id}
            </span>
          </div>
        </div>
      </div>

      {idea.related_topics && idea.related_topics.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-1">Related topics:</p>
          <div className="flex flex-wrap gap-1">
            {idea.related_topics.map((t, i) => (
              <span key={i} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">💡 Cơ hội:</span>{' '}
          {idea.opportunity_description}
        </p>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={generateScript}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Đang tạo...' : '✍️ Tạo Script (30 credits)'}
        </button>
      </div>
    </div>
  );
}
```

---

## Bước 3: IdeaFilters Component

**File:** `apps/web/components/ideas/idea-filters.tsx`

```typescript
'use client';

interface Props {
  confidence: string;
  setConfidence: (v: string) => void;
  search: string;
  setSearch: (v: string) => void;
  sortBy: string;
  setSortBy: (v: string) => void;
}

export function IdeaFilters({
  confidence,
  setConfidence,
  search,
  setSearch,
  sortBy,
  setSortBy,
}: Props) {
  return (
    <div className="bg-white p-4 rounded-lg shadow border mb-4">
      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Tìm kiếm
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo topic..."
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Confidence
          </label>
          <select
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="all">Tất cả</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Sắp xếp
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="gap_desc">Gap Score (cao → thấp)</option>
            <option value="gap_asc">Gap Score (thấp → cao)</option>
            <option value="date_desc">Mới nhất</option>
            <option value="alpha">A-Z</option>
          </select>
        </div>
      </div>
    </div>
  );
}
```

---

## Bước 4: RegenerateButton

**File:** `apps/web/components/ideas/regenerate-button.tsx`

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function RegenerateButton({ assistantId }: { assistantId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!confirm('Regenerate sẽ charge 5 credits. Tiếp tục?')) return;

    setLoading(true);
    try {
      const response = await fetch('/api/jobs/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          task_type: 'idea_generation',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/jobs/${data.job_id}`);
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
    >
      {loading ? 'Đang chạy...' : '🔄 Regenerate (5 credits)'}
    </button>
  );
}
```

---

## Bước 5: IdeasList Wrapper

**File:** `apps/web/components/ideas/ideas-list.tsx`

```typescript
'use client';

import { useState, useMemo } from 'react';
import { IdeaCard } from './idea-card';
import { IdeaFilters } from './idea-filters';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export function IdeasList({
  ideas,
  assistantId,
}: {
  ideas: Idea[];
  assistantId: string;
}) {
  const [confidence, setConfidence] = useState('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('gap_desc');

  const filteredIdeas = useMemo(() => {
    let result = [...ideas];

    if (confidence !== 'all') {
      result = result.filter((i) => i.confidence === confidence);
    }

    if (search) {
      const s = search.toLowerCase();
      result = result.filter((i) =>
        i.idea_topic.toLowerCase().includes(s)
      );
    }

    switch (sortBy) {
      case 'gap_desc':
        result.sort((a, b) => b.gap_score - a.gap_score);
        break;
      case 'gap_asc':
        result.sort((a, b) => a.gap_score - b.gap_score);
        break;
      case 'date_desc':
        // Assuming newest first by id (UUID v4 has timestamp prefix)
        break;
      case 'alpha':
        result.sort((a, b) => a.idea_topic.localeCompare(b.idea_topic));
        break;
    }

    return result;
  }, [ideas, confidence, search, sortBy]);

  return (
    <>
      <IdeaFilters
        confidence={confidence}
        setConfidence={setConfidence}
        search={search}
        setSearch={setSearch}
        sortBy={sortBy}
        setSortBy={setSortBy}
      />

      <p className="text-sm text-gray-500 mb-3">
        Hiển thị {filteredIdeas.length}/{ideas.length} ideas
      </p>

      {filteredIdeas.length === 0 ? (
        <p className="text-center text-gray-500 italic py-8">
          Không có idea nào khớp với filter.
        </p>
      ) : (
        <div className="space-y-4">
          {filteredIdeas.map((idea) => (
            <IdeaCard
              key={idea.id}
              idea={idea}
              assistantId={assistantId}
            />
          ))}
        </div>
      )}
    </>
  );
}
```

---

## Bước 6: Main Page

**File:** `apps/web/app/ideas/[assistant_id]/page.tsx`

```typescript
import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { IdeasList } from '@/components/ideas/ideas-list';
import { RegenerateButton } from '@/components/ideas/regenerate-button';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export default async function IdeasPage({
  params,
}: {
  params: Promise<{ assistant_id: string }>;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const { assistant_id } = await params;

  // Fetch assistant
  const asstRes = await apiFetch(`/api/assistants/${assistant_id}`, {}, token);
  if (asstRes.status === 404) notFound();
  const assistant = await asstRes.json();

  // Fetch ideas
  const res = await apiFetch(`/api/ideas/${assistant_id}`, {}, token);
  const ideas: Idea[] = res.ok ? await res.json() : [];

  // Stats
  const stats = {
    total: ideas.length,
    topScore: ideas.length > 0 ? Math.max(...ideas.map((i) => i.gap_score)) : 0,
    avgScore: ideas.length > 0
      ? Math.round(ideas.reduce((sum, i) => sum + i.gap_score, 0) / ideas.length)
      : 0,
    highCount: ideas.filter((i) => i.confidence === 'high').length,
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <Link
        href={`/assistants/${assistant_id}`}
        className="text-blue-600 hover:underline"
      >
        ← Quay lại Assistant
      </Link>

      <div className="flex items-center justify-between mt-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold">
            Ideas: {assistant.channel_name}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {stats.total} ideas • Top: {stats.topScore} • Avg: {stats.avgScore} •{' '}
            {stats.highCount} HIGH confidence
          </p>
        </div>
        <RegenerateButton assistantId={assistant_id} />
      </div>

      {ideas.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border">
          <div className="text-6xl mb-4">💡</div>
          <h2 className="text-xl font-semibold mb-2">
            Chưa có Idea nào cho kênh này
          </h2>
          <p className="text-gray-500 mb-6">
            Generate Ideas từ Deep Analysis sẽ charge 5 credits
          </p>
          <RegenerateButton assistantId={assistant_id} />
        </div>
      ) : (
        <IdeasList ideas={ideas} assistantId={assistant_id} />
      )}
    </main>
  );
}
```

---

## Bước 7: Verify

```bash
cd apps/web
pnpm dev
# Navigate http://localhost:3000/ideas/{assistant_id}
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task8-ideas.md
cat docs/plan/SKILL-ROUTING-sprint4-task8-ideas.md
cat docs/plan/PLAN-sprint4-task8-ideas.md
cat docs/plan/MSEW-sprint4-task8-ideas.md
cat docs/plan/ACCEPTANCE-sprint4-task8-ideas.md
```