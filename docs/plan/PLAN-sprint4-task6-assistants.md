# Sprint 4+ Task Group 6: Channel Assistants - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  CHANNEL ASSISTANTS FLOW                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → /projects/new (nhập URL)                                │
│     │                                                            │
│     ▼                                                            │
│  Backend tạo Channel Assistant (record trong DB)                  │
│     │                                                            │
│     ▼                                                            │
│  Redirect → /jobs/[job_id] (Celery collect)                     │
│     │                                                            │
│     ▼ (khi xong)                                                │
│  Redirect → /assistants/[id] (DNA)                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Pages Detail

### 1. /assistants (List)

**Type:** Server Component
**Data:** GET /api/assistants (returns user's assistants)

**Empty State:**
```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│              Bạn chưa có Channel Assistant nào                   │
│                                                                   │
│        Thu thập kênh YouTube để bắt đầu phân tích DNA            │
│                                                                   │
│              [📺 Tạo Channel Assistant mới]                       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Populated State:** Grid 3 cột (responsive)

### 2. /assistants/[id] (Detail)

**Type:** Server Component (với client action buttons)
**Data:**
- GET /api/assistants/[id]
- GET /api/jobs?assistant_id=[id] (recent jobs)

**Sections:**
1. Header (back button, name, delete button)
2. Channel metadata card
3. Action buttons (4 buttons)
4. Recent jobs list

## API Routes

### GET /api/assistants

Returns:
```typescript
[{
  id: string;
  channel_name: string;
  channel_thumbnail: string;
  channel_subscribers: number;
  total_videos_collected: number;
  quality_videos_count: number;
  viral_videos_count: number;
  status: 'collecting' | 'ready' | 'failed';
  has_analysis: boolean;
  scripts_count: number;
  last_job_at: string | null;
  created_at: string;
}]
```

### GET /api/assistants/[id]

Returns single assistant + recent_jobs

### DELETE /api/assistants/[id]

Soft delete (set is_deleted=true) hoặc hard delete
- Cascade delete: jobs, analysis, scripts, ideas
- Cần confirm dialog UI

## Backend API Reference

### Endpoint hiện có

```python
# apps/api/modules/module_2a/routes.py (đã có)
POST /api/collect/channel  # Returns channel_id, viral_count, etc.

# CẦN THÊM (Backend, không phải task này):
GET /api/assistants        # List user's assistants
GET /api/assistants/{id}   # Get one
DELETE /api/assistants/{id} # Delete
```

⚠️ **Lưu ý:** Task Group 6 chỉ làm UI + BFF proxy. Backend API `/api/assistants` cần được implement riêng (Task Group 11 hoặc theo roadmap mở rộng).

---

## BFF Proxy Pattern

```typescript
// /api/assistants/route.ts
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { NextResponse } from 'next/server';

export async function GET() {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    const response = await apiFetch('/api/assistants', {}, token);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch' },
      { status: 500 }
    );
  }
}
```

---

## Files to Create

### 1. Page Files

- `apps/web/app/assistants/page.tsx` - List page
- `apps/web/app/assistants/[id]/page.tsx` - Detail page

### 2. API Proxy Routes

- `apps/web/app/api/assistants/route.ts` - GET list
- `apps/web/app/api/assistants/[id]/route.ts` - GET + DELETE

### 3. Components

- `apps/web/components/assistant-card.tsx`
- `apps/web/components/assistant-actions.tsx`

---

## Constraints

1. **JWT enforced** ở mọi API route
2. **RLS isolation** verified (Task 5 RLS tests sẽ cover)
3. **Loading states** cho slow API calls
4. **Error states** khi backend fail
5. **No direct supabase calls** từ frontend (BFF only)