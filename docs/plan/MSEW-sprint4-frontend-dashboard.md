# Sprint 4 Task Group 4: Frontend Dashboard - MSEW

## Bước 1: Dashboard Page

**File:** `apps/web/app/dashboard/page.tsx`

```typescript
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { JobCard } from '@/components/job-card';

export default async function DashboardPage() {
  const token = getAccessToken();
  if (!token) redirect('/login');

  const response = await apiFetch('/api/jobs/recent', {}, token);
  const jobs = await response.json();

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <a href="/projects/new" className="bg-blue-600 text-white px-4 py-2 rounded">
          + Dự án mới
        </a>
      </div>

      <div className="grid gap-4">
        {jobs.map((job: any) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </main>
  );
}
```

---

## Bước 2: Job Card

**File:** `apps/web/components/job-card.tsx`

```typescript
'use client';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  created_at: string;
}

export function JobCard({ job }: { job: Job }) {
  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    succeeded: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <a
      href={`/jobs/${job.id}`}
      className="block p-4 border rounded hover:bg-gray-50"
    >
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold">{job.task_type}</h3>
          <p className="text-sm text-gray-500">
            {new Date(job.created_at).toLocaleString('vi-VN')}
          </p>
        </div>
        <span className={`px- Newark ${statusColors[job.status]}`}>
          {job.status} ({job.progress}%)
        </span>
      </div>
    </a>
  );
}
```

---

## Bước 3: New Project Page

**File:** `apps/web/app/projects/new/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function NewProjectPage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const response = await fetch('/api/channels/collect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ youtube_url: url }),
    });

    if (response.ok) {
      const data = await response.json();
      router.push(`/jobs/${data.job_id}`);
    } else {
      const error = await response.json();
      setError(error.detail || 'Failed');
    }
    setLoading(false);
  }

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Dự án mới</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            YouTube Channel URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/@channel"
            required
            className="w-full p-2 border rounded"
          />
        </div>
        {error && <p className="text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          {loading ? 'Đang xử lý...' : 'Bắt đầu'}
        </button>
      </form>
    </main>
  );
}
```

---

## Bước 4: Job Progress Page

**File:** `apps/web/app/jobs/[id]/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { createBrowserClient } from '@supabase/ssr';
import { SubProgressList } from '@/components/sub-progress-list';

interface Job {
  id: string;
  task_type: string;
  status: string;
  progress: number;
  sub_progress: Record<string, any>;
}

export default function JobProgressPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );

    // Initial fetch
    fetch(`/api/jobs/${params.id}`)
      .then((r) => r.json())
      .then(setJob);

    // Realtime subscription
    const channel = supabase
      .channel(`job-${params.id}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'jobs',
        filter: `id=eq.${params.id}`,
      }, (payload) => {
        setJob(payload.new as Job);
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [params.id]);

  if (!job) return <div>Loading...</div>;

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">{job.task_type}</h1>
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span>Tiến trình tổng</span>
          <span>{job.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>
      <SubProgressList subProgress={job.sub_progress} />
    </main>
  );
}
```

---

## Bước 5: Sub Progress List

**File:** `apps/web/components/sub-progress-list.tsx`

```typescript
interface SubProgress {
  [key: string]: { status: string; progress: number };
}

export function SubProgressList({ subProgress }: { subProgress: SubProgress }) {
  const entries = Object.entries(subProgress || {});

  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="p-3 border rounded">
          <div className="flex justify-between items-center">
            <span className="capitalize">{key.replace(/_/g, ' ')}</span>
            <span className={`text-sm px-2 py-1 rounded ${
              value.status === 'done' ? 'bg-green-100 text-green-800' :
              value.status === 'running' ? 'bg-blue-100 text-blue-800' :
              value.status === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {value.status} ({value.progress}%)
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-1">
            <div
              className="bg-blue-600 h-1 rounded-full"
              style={{ width: `${value.progress}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Bước 6: Script Editor Page

**File:** `apps/web/app/scripts/[id]/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { SceneTimeline } from '@/components/scene-timeline';

interface Script {
  id: string;
  topic: string;
  script: { title: string; hook: string; body: string; cta: string };
  scenes: any[];
}

export default function ScriptEditorPage({ params }: { params: { id: string } }) {
  const [script, setScript] = useState<Script | null>(null);

  useEffect(() => {
    fetch(`/api/scripts/${params.id}`)
      .then((r) => r.json())
      .then(setScript);
  }, [params.id]);

  if (!script) return <div>Loading...</div>;

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">{script.script.title}</h1>
      <p className="text-gray-600 mb-6">Chủ đề: {script.topic}</p>

      <div className="grid lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Hook (30 giây)</h2>
          <textarea
            value={script.script.hook}
            className="w-full p-3 border rounded h-32"
          />

          <h2 className="text-xl font-semibold mt-4 mb-2">Body</h2>
          <textarea
            value={script.script.body}
            className="w-full p-3 border rounded h-96"
          />

          <h2 className="text-xl font-semibold mt-4 mb-2">CTA</h2>
          <textarea
            value={script.script.cta}
            className="w-full p-3 border rounded h-24"
          />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">Scenes</h2>
          <SceneTimeline scenes={script.scenes} />
        </div>
      </div>
    </main>
  );
}
```

---

## Bước 7: Scene Timeline

**File:** `apps/web/components/scene-timeline.tsx`

```typescript
interface Scene {
  scene_number: number;
  start_time: number;
  end_time: number;
  duration_seconds: number;
  text: string;
  broll_translations: Array<{ en: string; pexels_query: string }>;
}

export function SceneTimeline({ scenes }: { scenes: Scene[] }) {
  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${String(sec).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-2">
      {scenes.map((scene) => (
        <div key={scene.scene_number} className="p-3 border rounded">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Scene {scene.scene_number}</span>
            <span>{fmt(scene.start_time)} - {fmt(scene.end_time)}</span>
          </div>
          <p className="text-sm">{scene.text.slice(0, 100)}...</p>
          {scene.broll_translations?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {scene.broll_translations.map((t, i) => (
                <span key={i} className="text-xs bg-blue-100 px-2 py-1 rounded">
                  {t.pexels_query}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

## Bước 8: Verify

```bash
cd apps/web
pnpm dev
# Mở http://localhost:3000/dashboard
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-frontend-dashboard.md
cat docs/plan/SKILL-ROUTING-sprint4-frontend-dashboard.md
cat docs/plan/PLAN-sprint4-frontend-dashboard.md
cat docs/plan/MSEW-sprint4-frontend-dashboard.md
cat docs/plan/ACCEPTANCE-sprint4-frontend-dashboard.md
```
