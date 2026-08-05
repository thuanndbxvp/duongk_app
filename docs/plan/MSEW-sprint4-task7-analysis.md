# Sprint 4+ Task Group 7: Deep Analysis - MSEW

## Checklist

- [ ] Bước 1: API proxy route
- [ ] Bước 2: OutputCard + JsonViewer components
- [ ] Bước 3: 6 tab components
- [ ] Bước 4: AnalysisTabs wrapper
- [ ] Bước 5: ReanalyzeButton
- [ ] Bước 6: Main page
- [ ] Bước 7: Verify

---

## Bước 1: API Proxy

**File:** `apps/web/app/api/analysis/[assistant_id]/route.ts`

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
      `/api/analysis/${assistant_id}`,
      {},
      token
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function POST(
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
      `/api/analysis/${assistant_id}/reanalyze`,
      { method: 'POST' },
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

## Bước 2: JsonViewer Component

**File:** `apps/web/components/analysis/json-viewer.tsx`

```typescript
'use client';

import { useState } from 'react';

export function JsonViewer({ data }: { data: any }) {
  const [expanded, setExpanded] = useState(false);

  if (data === null || data === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }

  if (typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
    return <span className="font-mono text-sm">{String(data)}</span>;
  }

  if (Array.isArray(data)) {
    return (
      <div className="font-mono text-sm">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-blue-600 hover:underline"
        >
          {expanded ? '▼' : '▶'} Array({data.length})
        </button>
        {expanded && (
          <pre className="ml-4 mt-2 bg-gray-50 p-2 rounded overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  // Object
  return (
    <div className="font-mono text-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-blue-600 hover:underline"
      >
        {expanded ? '▼' : '▶'} Object
      </button>
      {expanded && (
        <pre className="ml-4 mt-2 bg-gray-50 p-2 rounded overflow-x-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
```

---

## Bước 3: OutputCard Component

**File:** `apps/web/components/analysis/output-card.tsx`

```typescript
import { JsonViewer } from './json-viewer';

interface OutputCardProps {
  number: number;
  title: string;
  description: string;
  data: any;
  cost?: number;
}

export function OutputCard({ number, title, description, data, cost }: OutputCardProps) {
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
        {cost !== undefined && cost > 0 && (
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

## Bước 4: Tab Components

### DeterministicTab

**File:** `apps/web/components/analysis/deterministic-tab.tsx`

```typescript
import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_1_metadata: any;
    output_2_tags: any;
    output_3_performance: any;
    output_4_optimal_duration: any;
  };
}

export function DeterministicTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={1}
        title="Metadata Analysis"
        description="Thống kê tổng quan về videos"
        data={outputs.output_1_metadata}
      />
      <OutputCard
        number={2}
        title="Tags Analysis"
        description="Phân tích tags và co-occurrence"
        data={outputs.output_2_tags}
      />
      <OutputCard
        number={3}
        title="Performance Reports"
        description="Best/worst videos + Consistency Score (A5)"
        data={outputs.output_3_performance}
      />
      <OutputCard
        number={4}
        title="Optimal Duration (A4)"
        description="Độ dài video tối ưu dựa trên engagement"
        data={outputs.output_4_optimal_duration}
      />
    </div>
  );
}
```

### NLPTab

**File:** `apps/web/components/analysis/nlp-tab.tsx`

```typescript
import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_5_consistency: any;
    output_6_pacing: any;
    output_7_sentiment: any;
  };
}

export function NLPTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={5}
        title="Consistency Score (A5)"
        description="Độ nhất quán của kênh (0-100)"
        data={outputs.output_5_consistency}
      />
      <OutputCard
        number={6}
        title="Pacing Profile"
        description="WPM (words per minute) và độ dài câu"
        data={outputs.output_6_pacing}
      />
      <OutputCard
        number={7}
        title="Sentiment Distribution"
        description="Phân bố sentiment (positive/neutral/negative)"
        data={outputs.output_7_sentiment}
      />
    </div>
  );
}
```

### LLMTab

**File:** `apps/web/components/analysis/llm-tab.tsx`

```typescript
import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_8_hook: any;
    output_9_structure: any;
    output_10_emotion: any;
    output_11_mimic_rules: any;
  };
}

export function LLMTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={8}
        title="Hook Analysis"
        description="Phân tích Hook patterns bằng GPT-4o"
        data={outputs.output_8_hook}
        cost={0.02}
      />
      <OutputCard
        number={9}
        title="Structural Formula"
        description="Công thức cấu trúc video"
        data={outputs.output_9_structure}
        cost={0.02}
      />
      <OutputCard
        number={10}
        title="Emotion Distribution"
        description="Phân bố cảm xúc (PhoBERT + j-hartmann)"
        data={outputs.output_10_emotion}
      />
      <OutputCard
        number={11}
        title="Mimic Rules"
        description="Quy tắc bắt chước phong cách kênh"
        data={outputs.output_11_mimic_rules}
        cost={0.02}
      />
    </div>
  );
}
```

### InsightsTab

**File:** `apps/web/components/analysis/insights-tab.tsx`

```typescript
import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_12_insights: any;
    output_13_ideas: any;
  };
}

export function InsightsTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={12}
        title="Hidden Insights"
        description="Phát hiện ẩn (Chi-square + LLM narrate)"
        data={outputs.output_12_insights}
        cost={0.05}
      />
      <OutputCard
        number={13}
        title="Idea Opportunities (A14)"
        description="Untapped opportunities (Gap Score)"
        data={outputs.output_13_ideas}
      />
    </div>
  );
}
```

### ThumbnailTab

**File:** `apps/web/components/analysis/thumbnail-tab.tsx`

```typescript
import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_14_thumbnail: any;
  };
}

export function ThumbnailTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={14}
        title="Thumbnail Analysis"
        description="Phân tích thumbnail bằng GPT-4o Vision"
        data={outputs.output_14_thumbnail}
        cost={0.10}
      />
    </div>
  );
}
```

### OverviewTab

**File:** `apps/web/components/analysis/overview-tab.tsx`

```typescript
interface Props {
  data: any;
}

export function OverviewTab({ data }: Props) {
  const completedOutputs = Object.keys(data.outputs || {}).length;
  
  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">14 Outputs</div>
        <div className="text-3xl font-bold mt-1">
          {completedOutputs}/14
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {completedOutputs === 14 ? '✅ Hoàn thành' : '⏳ Đang xử lý'}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">Lần phân tích cuối</div>
        <div className="text-xl font-bold mt-1">
          {new Date(data.computed_at).toLocaleString('vi-VN')}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Version {data.version}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">Tổng chi phí</div>
        <div className="text-3xl font-bold mt-1 text-green-600">
          ${(data.total_cost_usd || 0).toFixed(3)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          LLM + Vision API
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6 md:col-span-3">
        <h3 className="font-bold mb-3">Output Categories</h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-sm">
          <div className="bg-blue-50 p-3 rounded">
            <div className="font-semibold">Deterministic</div>
            <div className="text-xs">Outputs 1-4</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="font-semibold">NLP</div>
            <div className="text-xs">Outputs 5-7</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="font-semibold">LLM</div>
            <div className="text-xs">Outputs 8-11</div>
          </div>
          <div className="bg-orange-50 p-3 rounded">
            <div className="font-semibold">Insights</div>
            <div className="text-xs">Outputs 12-13</div>
          </div>
          <div className="bg-pink-50 p-3 rounded">
            <div className="font-semibold">Thumbnail</div>
            <div className="text-xs">Output 14</div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Bước 5: Tabs Container

**File:** `apps/web/components/analysis/analysis-tabs.tsx`

```typescript
'use client';

import { useState } from 'react';
import { OverviewTab } from './overview-tab';
import { DeterministicTab } from './deterministic-tab';
import { NLPTab } from './nlp-tab';
import { LLMTab } from './llm-tab';
import { InsightsTab } from './insights-tab';
import { ThumbnailTab } from './thumbnail-tab';

interface Props {
  data: any;
}

const TABS = [
  { id: 'overview', label: 'Tổng quan' },
  { id: 'deterministic', label: 'Deterministic' },
  { id: 'nlp', label: 'NLP' },
  { id: 'llm', label: 'LLM' },
  { id: 'insights', label: 'Insights' },
  { id: 'thumbnail', label: 'Thumbnail' },
];

export function AnalysisTabs({ data }: Props) {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <>
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-1 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'deterministic' && (
          <DeterministicTab outputs={data.outputs} />
        )}
        {activeTab === 'nlp' && <NLPTab outputs={data.outputs} />}
        {activeTab === 'llm' && <LLMTab outputs={data.outputs} />}
        {activeTab === 'insights' && <InsightsTab outputs={data.outputs} />}
        {activeTab === 'thumbnail' && <ThumbnailTab outputs={data.outputs} />}
      </div>
    </>
  );
}
```

---

## Bước 6: ReanalyzeButton

**File:** `apps/web/components/analysis/reanalyze-button.tsx`

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function ReanalyzeButton({ assistantId }: { assistantId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!confirm('Re-analyze sẽ charge 50 credits. Tiếp tục?')) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/analysis/${assistantId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/jobs/${data.job_id}`);
      } else {
        const err = await response.json();
        alert(err.detail || err.error || 'Failed');
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
      {loading ? 'Đang chạy...' : '🔄 Re-analyze (50 credits)'}
    </button>
  );
}
```

---

## Bước 7: Main Page

**File:** `apps/web/app/analysis/[assistant_id]/page.tsx`

```typescript
import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { AnalysisTabs } from '@/components/analysis/analysis-tabs';
import { ReanalyzeButton } from '@/components/analysis/reanalyze-button';

export default async function AnalysisPage({
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

  // Fetch analysis
  const res = await apiFetch(`/api/analysis/${assistant_id}`, {}, token);

  // Empty state if not analyzed yet
  if (res.status === 404) {
    return (
      <main className="container mx-auto p-8 max-w-3xl">
        <Link
          href={`/assistants/${assistant_id}`}
          className="text-blue-600 hover:underline"
        >
          ← Quay lại Assistant
        </Link>
        <div className="text-center py-16 bg-white rounded-lg border mt-6">
          <div className="text-6xl mb-4">🧠</div>
          <h1 className="text-2xl font-bold mb-2">
            Chưa chạy Deep Analysis cho {assistant.channel_name}
          </h1>
          <p className="text-gray-500 mb-6">
            Phân tích 14 outputs sẽ charge 50 credits (~2-3 phút)
          </p>
          <ReanalyzeButton assistantId={assistant_id} />
        </div>
      </main>
    );
  }

  if (!res.ok) {
    return (
      <main className="container mx-auto p-8">
        <p className="text-red-600">Failed to load analysis.</p>
      </main>
    );
  }

  const data = await res.json();

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <Link
        href={`/assistants/${assistant_id}`}
        className="text-blue-600 hover:underline"
      >
        ← Quay lại Assistant
      </Link>
      
      <div className="flex items-center justify-between mt-4 mb-6">
        <h1 className="text-3xl font-bold">
          Deep Analysis: {assistant.channel_name}
        </h1>
        <ReanalyzeButton assistantId={assistant_id} />
      </div>

      <AnalysisTabs data={data} />
    </main>
  );
}
```

---

## Bước 8: Verify

```bash
cd apps/web
pnpm dev
# Navigate http://localhost:3000/analysis/{assistant_id}
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task7-analysis.md
cat docs/plan/SKILL-ROUTING-sprint4-task7-analysis.md
cat docs/plan/PLAN-sprint4-task7-analysis.md
cat docs/plan/MSEW-sprint4-task7-analysis.md
cat docs/plan/ACCEPTANCE-sprint4-task7-analysis.md
```