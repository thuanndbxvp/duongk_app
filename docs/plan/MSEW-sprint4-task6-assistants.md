# Sprint 4+ Task Group 6: Channel Assistants - MSEW

## Checklist

- [ ] Bước 1: API proxy route GET /api/assistants
- [ ] Bước 2: API proxy route GET/DELETE /api/assistants/[id]
- [ ] Bước 3: Component AssistantCard
- [ ] Bước 4: Component AssistantActions
- [ ] Bước 5: Page /assistants (list)
- [ ] Bước 6: Page /assistants/[id] (detail)
- [ ] Bước 7: Verify

---

## Bước 1: API Proxy List

**File:** `apps/web/app/api/assistants/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET() {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const response = await apiFetch('/api/assistants', {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

---

## Bước 2: API Proxy Detail

**File:** `apps/web/app/api/assistants/[id]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;
  
  try {
    const response = await apiFetch(`/api/assistants/${id}`, {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;
  
  try {
    const response = await apiFetch(`/api/assistants/${id}`, {
      method: 'DELETE',
    }, token);
    
    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

---

## Bước 3: AssistantCard Component

**File:** `apps/web/components/assistant-card.tsx`

```typescript
import Link from 'next/link';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_subscribers: number;
  total_videos_collected: number;
  viral_videos_count: number;
  status: 'collecting' | 'ready' | 'failed';
  has_analysis: boolean;
  scripts_count: number;
  last_job_at: string | null;
  created_at: string;
}

export function AssistantCard({ assistant }: { assistant: Assistant }) {
  const statusColors = {
    ready: 'bg-green-100 text-green-800',
    collecting: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
  };

  const formatSubs = (n: number): string => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <Link
      href={`/assistants/${assistant.id}`}
      className="block bg-white border rounded-lg p-5 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start gap-4">
        <img
          src={assistant.channel_thumbnail || '/placeholder.png'}
          alt={assistant.channel_name}
          className="w-16 h-16 rounded-full object-cover"
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg truncate">{assistant.channel_name}</h3>
          <p className="text-sm text-gray-500">
            {formatSubs(assistant.channel_subscribers)} subscribers
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-800">
            {assistant.total_videos_collected}
          </div>
          <div className="text-xs text-gray-500">videos</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-orange-600">
            {assistant.viral_videos_count}
          </div>
          <div className="text-xs text-gray-500">viral</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">
            {assistant.scripts_count}
          </div>
          <div className="text-xs text-gray-500">scripts</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[assistant.status]}`}>
          {assistant.status}
        </span>
        {assistant.has_analysis && (
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
            🧠 analyzed
          </span>
        )}
      </div>
    </Link>
  );
}
```

---

## Bước 4: AssistantActions Component

**File:** `apps/web/components/assistant-actions.tsx`

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface AssistantActionsProps {
  assistantId: string;
  hasAnalysis: boolean;
  hasScripts: boolean;
}

export function AssistantActions({
  assistantId,
  hasAnalysis,
  hasScripts,
}: AssistantActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  async function triggerJob(taskType: string, redirectToJobs = true) {
    setLoading(taskType);
    try {
      const response = await fetch(`/api/jobs/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assistant_id: assistantId, task_type: taskType }),
      });

      if (response.ok) {
        const data = await response.json();
        if (redirectToJobs) {
          router.push(`/jobs/${data.job_id}`);
        } else {
          router.refresh();
        }
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to start job');
      }
    } finally {
      setLoading(null);
    }
  }

  const actions = [
    {
      id: 'analyze',
      label: 'Deep Analysis',
      emoji: '🧠',
      cost: 50,
      taskType: 'deep_analysis',
      disabled: false,
    },
    {
      id: 'ideas',
      label: 'Generate Ideas',
      emoji: '💡',
      cost: 5,
      taskType: 'idea_generation',
      disabled: !hasAnalysis,
      tooltip: !hasAnalysis ? 'Cần chạy Deep Analysis trước' : undefined,
    },
    {
      id: 'script',
      label: 'Generate Script',
      emoji: '✍️',
      cost: 30,
      taskType: 'script_generate',
      disabled: !hasAnalysis,
      tooltip: !hasAnalysis ? 'Cần chạy Deep Analysis trước' : undefined,
    },
    {
      id: 'history',
      label: 'Xem Scripts',
      emoji: '📜',
      cost: 0,
      taskType: 'history',
      disabled: !hasScripts,
      action: () => router.push(`/scripts?assistant_id=${assistantId}`),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {actions.map((action) => (
        <button
          key={action.id}
          disabled={action.disabled || loading === action.taskType}
          onClick={() => {
            if (action.taskType === 'history' && action.action) {
              action.action();
            } else {
              triggerJob(action.taskType);
            }
          }}
          title={action.tooltip}
          className="p-4 border-2 border-dashed rounded-lg hover:border-blue-500 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <div className="text-3xl mb-2">{action.emoji}</div>
          <div className="font-semibold">{action.label}</div>
          {action.cost > 0 && (
            <div className="text-xs text-gray-500 mt-1">{action.cost} credits</div>
          )}
          {loading === action.taskType && (
            <div className="text-xs text-blue-600 mt-1">Đang xử lý...</div>
          )}
        </button>
      ))}
    </div>
  );
}
```

---

## Bước 5: List Page

**File:** `apps/web/app/assistants/page.tsx`

```typescript
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AssistantCard } from '@/components/assistant-card';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_subscribers: number;
  total_videos_collected: number;
  viral_videos_count: number;
  status: 'collecting' | 'ready' | 'failed';
  has_analysis: boolean;
  scripts_count: number;
  last_job_at: string | null;
  created_at: string;
}

export default async function AssistantsPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const response = await apiFetch('/api/assistants', {}, token);
  const assistants: Assistant[] = response.ok ? await response.json() : [];

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Channel Assistants</h1>
          <p className="text-gray-500 mt-1">
            DNA và phong cách các kênh YouTube của bạn
          </p>
        </div>
        <Link
          href="/projects/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Tạo mới
        </Link>
      </div>

      {assistants.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border">
          <div className="text-6xl mb-4">📺</div>
          <h2 className="text-xl font-semibold mb-2">
            Bạn chưa có Channel Assistant nào
          </h2>
          <p className="text-gray-500 mb-6">
            Thu thập kênh YouTube để bắt đầu phân tích DNA
          </p>
          <Link
            href="/projects/new"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            📺 Tạo Channel Assistant mới
          </Link>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {assistants.length} Channel Assistant{assistants.length !== 1 ? 's' : ''}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {assistants.map((assistant) => (
              <AssistantCard key={assistant.id} assistant={assistant} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
```

---

## Bước 6: Detail Page

**File:** `apps/web/app/assistants/[id]/page.tsx`

```typescript
import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AssistantActions } from '@/components/assistant-actions';

interface Assistant {
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_id: string;
  channel_subscribers: number;
  total_videos_collected: number;
  quality_videos_count: number;
  viral_videos_count: number;
  status: string;
  has_analysis: boolean;
  scripts_count: number;
  created_at: string;
}

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  created_at: string;
}

export default async function AssistantDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const { id } = await params;

  // Fetch assistant
  const res = await apiFetch(`/api/assistants/${id}`, {}, token);
  if (res.status === 404) notFound();
  if (!res.ok) redirect('/assistants');

  const assistant: Assistant = await res.json();

  // Fetch recent jobs (optional)
  const jobsRes = await apiFetch(`/api/jobs?assistant_id=${id}&limit=5`, {}, token);
  const recentJobs: Job[] = jobsRes.ok ? await jobsRes.json() : [];

  const formatSubs = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <div className="flex items-center mb-6">
        <Link href="/assistants" className="text-blue-600 hover:underline">
          ← Quay lại danh sách
        </Link>
      </div>

      {/* Header */}
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
        <div className="flex items-start gap-6">
          <img
            src={assistant.channel_thumbnail || '/placeholder.png'}
            alt={assistant.channel_name}
            className="w-24 h-24 rounded-full object-cover"
          />
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">{assistant.channel_name}</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Subscribers</div>
                <div className="font-semibold">
                  {formatSubs(assistant.channel_subscribers)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Videos</div>
                <div className="font-semibold">
                  {assistant.total_videos_collected}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Viral</div>
                <div className="font-semibold text-orange-600">
                  {assistant.viral_videos_count}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Status</div>
                <div className="font-semibold">{assistant.status}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Hành động</h2>
        <AssistantActions
          assistantId={assistant.id}
          hasAnalysis={assistant.has_analysis}
          hasScripts={assistant.scripts_count > 0}
        />
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h2 className="text-lg font-semibold mb-4">Jobs gần đây</h2>
        {recentJobs.length === 0 ? (
          <p className="text-gray-500 italic">Chưa có job nào.</p>
        ) : (
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <Link
                key={job.id}
                href={`/jobs/${job.id}`}
                className="block p-3 border rounded hover:bg-gray-50"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium capitalize">
                      {job.task_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleString('vi-VN')}
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="px-2 py-1 bg-gray-100 rounded-full">
                      {job.status} ({job.progress}%)
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
```

---

## Bước 7: Verify

```bash
cd apps/web
pnpm dev
# Navigate http://localhost:3000/assistants
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task6-assistants.md
cat docs/plan/SKILL-ROUTING-sprint4-task6-assistants.md
cat docs/plan/PLAN-sprint4-task6-assistants.md
cat docs/plan/MSEW-sprint4-task6-assistants.md
cat docs/plan/ACCEPTANCE-sprint4-task6-assistants.md
```