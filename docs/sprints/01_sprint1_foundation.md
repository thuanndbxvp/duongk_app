# 01 — Sprint 1: Foundation (Tuần 1-2)

> **Mục tiêu:** Setup monorepo, Supabase schema + RLS, Module 0-Lite (auth + credit hold/commit/release), FastAPI + Celery skeleton, Realtime subscription.
> **Outcome cuối sprint:** User đăng ký → đăng nhập → có 1000 mock credits → tạo 1 job "niche validate" thật (mock LLM) → thấy progress realtime → job hoàn thành → credits được hold/commit đúng.

---

## 1. Sprint backlog

| # | Task | Effort | Owner | Status |
|---|------|--------|-------|--------|
| 1.1 | Monorepo skeleton (Nx/Turborepo/pnpm workspace) | 4h | TBD | pending |
| 1.2 | Supabase project setup + env vars | 1h | TBD | pending |
| 1.3 | SQL migrations #1-#10 (xem §3 dưới) | 6h | TBD | pending |
| 1.4 | RLS policies cho 9 tables | 3h | TBD | pending |
| 1.5 | Next.js 15 init (App Router + Tailwind + shadcn) | 4h | TBD | pending |
| 1.6 | Supabase Auth pages (login/register/logout) | 4h | TBD | pending |
| 1.7 | FastAPI skeleton (JWT verify dependency) | 4h | TBD | pending |
| 1.8 | Celery worker skeleton (Redis broker) | 3h | TBD | pending |
| 1.9 | Credit system (hold/commit/release SQL functions) | 5h | TBD | pending |
| 1.10 | Realtime subscription (jobs.progress) | 3h | TBD | pending |
| 1.11 | Mock `niche_validate` Celery task (fake 3s) | 2h | TBD | pending |
| 1.12 | End-to-end demo (URL → progress → done) | 4h | TBD | pending |
| 1.13 | Observability: Sentry + Prometheus setup | 3h | TBD | pending |
| 1.14 | Docker Compose (postgres + redis + api + worker + web) | 4h | TBD | pending |
| **1.15** | **Local ML models singleton** (Celery worker_init + max_tasks_per_child) | 3h | TBD | pending |
| **1.16** | **JWT verify với SUPABASE_JWT_SECRET** (PyJWT HS256, không verify_signature:False) | 2h | TBD | pending |
| **1.17** | **Type sync script** (`scripts/sync_types.py` + datamodel-code-generator + Zod) | 2h | TBD | pending |

**Total estimated:** ~57h = 2 tuần (2 devs fulltime)

> **v4.2 D-series tasks** (1.15, 1.16, 1.17) đã được thêm vào Sprint 1 backlog từ review Tech. Xem chi tiết Appendix N trong PRD v4.

---

## 2. Architecture decisions ghi rõ

### 2.1. Monorepo tool: **pnpm workspaces**
**Lý do:**
- Nhanh nhất (symlink + content-addressable store)
- Turbo cũng OK nhưng pnpm đơn giản hơn cho team nhỏ
- Hỗ trợ tốt cho Python monorepo (pip + pyproject.toml) qua sidecar

```json
// pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### 2.2. Python package manager: **uv**
**Lý do:** Cực nhanh (Rust-based), tương thích pip, có lock file tốt.
Alternative: Poetry (chậm hơn nhưng trưởng thành).

```toml
# apps/api/pyproject.toml
[project]
name = "appdk-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic>=2.9",
    "supabase>=2.8",
    "celery>=5.4",
    "redis>=5.0",
    "python-jose[cryptography]>=3.3",  # JWT
    "pyjwt>=2.9",
    "python-dotenv>=1.0",
    "httpx>=0.27",  # cho API calls
]
```

### 2.3. Frontend package manager: **pnpm** (cùng với workspace)

### 2.4. ORM: **Không dùng ORM** — dùng `supabase-py` + raw SQL migrations
**Lý do:**
- Schema của mình đã tối ưu cho Postgres (jsonb, vector)
- ORM che giấu performance characteristics
- `supabase-py` đã wrap PostgREST API + realtime

### 2.5. Realtime: **Supabase Realtime** (đã chốt, không dùng WebSocket riêng)

---

## 3. SQL migrations cho Sprint 1

> File naming: `NNNN_short_description.sql`. Counter bắt đầu từ 0001.

### Migration `0001_init_users.sql`

```sql
-- Core users table (extends Supabase auth.users)
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  credits INT NOT NULL DEFAULT 1000,  -- mock for Phase 1
  tier TEXT NOT NULL DEFAULT 'free',  -- free | pro | agency
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger: tự tạo users row khi auth.users có row mới
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

### Migration `0002_jobs.sql`

```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  task_type TEXT NOT NULL,
    -- 'niche_validate' | 'research_validate' | 'channel_collection'
    -- | 'dna_extract' | 'script_generate' | 'scene_breakdown' | 'deep_channel_analysis'
  celery_task_id TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
    -- pending | running | succeeded | failed | cancelled
  progress INT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  input_payload JSONB,
  result_payload JSONB,
  error_message TEXT,
  credits_held INT DEFAULT 0,
  sub_progress JSONB DEFAULT '{}'::jsonb,  -- từ PRD v4 Appendix K.1
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX idx_jobs_task_type ON jobs(task_type);

-- Updated_at trigger
CREATE TRIGGER set_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION moddatetime(updated_at);
```

### Migration `0003_credit_transactions.sql`

```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  action TEXT NOT NULL CHECK (action IN
    ('hold', 'commit', 'release', 'topup', 'admin_adjust', 'refund_partial')),
  amount INT NOT NULL,  -- signed: negative = deduct
  balance_after INT NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credit_tx_user ON credit_transactions(user_id, created_at DESC);
CREATE INDEX idx_credit_tx_job ON credit_transactions(job_id);
```

### Migration `0004_api_usage_logs.sql`

```sql
-- Để Sprint 2+ dùng, Sprint 1 chỉ tạo table
CREATE TABLE api_usage_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  provider TEXT NOT NULL,
  operation TEXT NOT NULL,
  input_tokens INT,
  output_tokens INT,
  cost_usd NUMERIC(10,6),
  quota_units INT,
  api_key_id TEXT,
  status_code INT,
  duration_ms INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_usage_provider_date ON api_usage_logs(provider, created_at DESC);
CREATE INDEX idx_api_usage_user_date ON api_usage_logs(user_id, created_at DESC);
```

### Migration `0005_quota_ledger.sql`

```sql
-- Sprint 2 sẽ populate, Sprint 1 chỉ tạo
CREATE TABLE quota_ledger (
  id BIGSERIAL PRIMARY KEY,
  api_key_id TEXT NOT NULL,
  date DATE NOT NULL,
  units_used INT NOT NULL DEFAULT 0,
  units_limit INT NOT NULL DEFAULT 10000,
  UNIQUE(api_key_id, date)
);
```

### Migration `0006_credit_hold_commit.sql`

```sql
-- Atomic credit operations
-- (Sprint 1 MVP: chỉ cần hold/commit/release; refund_partial là Sprint 2)
CREATE OR REPLACE FUNCTION hold_credits(
  p_user_id UUID,
  p_job_id UUID,
  p_amount INT
) RETURNS TABLE(success BOOLEAN, new_balance INT) AS $$
DECLARE
  v_balance INT;
BEGIN
  -- Try to deduct
  UPDATE users
  SET credits = credits - p_amount,
      updated_at = NOW()
  WHERE id = p_user_id AND credits >= p_amount
  RETURNING credits INTO v_balance;
  
  IF v_balance IS NULL THEN
    -- Insufficient
    RETURN QUERY SELECT FALSE, (SELECT credits FROM users WHERE id = p_user_id);
    RETURN;
  END IF;
  
  -- Log transaction
  INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
  VALUES (p_user_id, p_job_id, 'hold', -p_amount, v_balance,
          format('Held %s credits for job', p_amount));
  
  -- Update job
  UPDATE jobs SET credits_held = p_amount WHERE id = p_job_id;
  
  RETURN QUERY SELECT TRUE, v_balance;
END;
$$ LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION release_credits(
  p_user_id UUID,
  p_job_id UUID
) RETURNS INT AS $$
DECLARE
  v_held INT;
  v_new_balance INT;
BEGIN
  SELECT credits_held INTO v_held FROM jobs WHERE id = p_job_id;
  IF v_held IS NULL OR v_held = 0 THEN
    RETURN 0;
  END IF;
  
  UPDATE users
  SET credits = credits + v_held, updated_at = NOW()
  WHERE id = p_user_id
  RETURNING credits INTO v_new_balance;
  
  INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
  VALUES (p_user_id, p_job_id, 'release', v_held, v_new_balance,
          format('Refunded %s credits (job failed)', v_held));
  
  UPDATE jobs SET credits_held = 0 WHERE id = p_job_id;
  RETURN v_held;
END;
$$ LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION commit_credits(
  p_user_id UUID,
  p_job_id UUID
) RETURNS VOID AS $$
DECLARE
  v_held INT;
  v_new_balance INT;
BEGIN
  SELECT credits_held, status INTO v_held, ...;
  -- Just log the commit, balance không đổi
  ...
END;
$$ LANGUAGE plpgsql;
```

### Migration `0007_rls_policies.sql`

```sql
-- users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_self" ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "user_can_update_self" ON users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- jobs
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_jobs" ON jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "user_can_insert_own_jobs" ON jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- (KHÔNG cho user update/delete jobs — worker dùng service_role)

-- credit_transactions
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_credit_tx" ON credit_transactions FOR SELECT
  USING (auth.uid() = user_id);

-- api_usage_logs (admin only)
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;
-- (no user policy — service_role only)

-- quota_ledger (admin only)
ALTER TABLE quota_ledger ENABLE ROW LEVEL SECURITY;
```

### Migration `0008_seed_data.sql` (chỉ cho dev)

```sql
-- Seed 1 test channel + 1 test user
INSERT INTO auth.users (id, email) VALUES
  ('11111111-1111-1111-1111-111111111111', 'dev@appdk.local');

INSERT INTO public.users (id, email, credits, tier) VALUES
  ('11111111-1111-1111-1111-111111111111', 'dev@appdk.local', 1000, 'free');
```

---

## 4. FastAPI scaffold

### `apps/api/main.py`
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from apps.api.routers import users, jobs, auth
from apps.api.dependencies.supabase import get_supabase_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(title="AppDK API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router, prefix='/api/auth', tags=['auth'])
app.include_router(users.router, prefix='/api/users', tags=['users'])
app.include_router(jobs.router, prefix='/api/jobs', tags=['jobs'])

@app.get('/health')
async def health():
    return {'status': 'ok'}
```

### `apps/api/dependencies/supabase.py`
- (Canonical example xem `00_shared_context.md` §5.1)

### `apps/api/routers/users.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.api.dependencies.supabase import get_supabase_user, get_supabase_admin

router = APIRouter()

class UserCredits(BaseModel):
    credits: int
    tier: str

@router.get('/me', response_model=UserCredits)
async def get_me(user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    result = admin.table('users').select('credits, tier').eq('id', user_id).single().execute()
    if not result.data:
        raise HTTPException(404, 'User not found')
    return UserCredits(**result.data)
```

### `apps/api/routers/jobs.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_user, get_supabase_admin
from apps.worker.tasks.niche_validate import niche_validate_task

router = APIRouter()

class CreateJobRequest(BaseModel):
    task_type: str
    input_payload: dict
    credits_to_hold: int

class JobResponse(BaseModel):
    id: str
    status: str
    progress: int

@router.post('/', response_model=JobResponse, status_code=201)
async def create_job(
    req: CreateJobRequest,
    user_id: str = Depends(get_supabase_user),
):
    admin = get_supabase_admin()
    
    # 1. Insert job (status=pending)
    job_result = admin.table('jobs').insert({
        'user_id': user_id,
        'task_type': req.task_type,
        'input_payload': req.input_payload,
        'status': 'pending',
    }).execute()
    job = job_result.data[0]
    job_id = job['id']
    
    # 2. Hold credits
    hold_result = admin.rpc('hold_credits', {
        'p_user_id': user_id,
        'p_job_id': job_id,
        'p_amount': req.credits_to_hold,
    }).execute()
    
    if not hold_result.data[0]['success']:
        # Insufficient credits → rollback
        admin.table('jobs').delete().eq('id', job_id).execute()
        raise HTTPException(402, 'Insufficient credits')
    
    # 3. Enqueue Celery task
    task = niche_validate_task.delay(job_id=job_id, **req.input_payload)
    
    # 4. Update celery_task_id
    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()
    
    return JobResponse(id=job_id, status='pending', progress=0)


@router.get('/{job_id}', response_model=JobResponse)
async def get_job(
    job_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    admin = get_supabase_admin()
    result = admin.table('jobs').select('id, status, progress') \
        .eq('id', str(job_id)) \
        .eq('user_id', user_id) \
        .single().execute()
    
    if not result.data:
        raise HTTPException(404, 'Job not found')
    return JobResponse(**result.data)
```

---

## 5. Celery worker scaffold

### `apps/worker/celery_app.py`
```python
from celery import Celery

celery_app = Celery(
    'appdk',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND'),
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'apps.worker.tasks.niche_validate.*': {'queue': 'high'},
        'apps.worker.tasks.dna_extract.*': {'queue': 'high'},
        'apps.worker.tasks.script_generate.*': {'queue': 'normal'},
    },
)
```

### `apps/worker/tasks/niche_validate.py` (Mock for Sprint 1)
```python
from apps.worker.celery_app import celery_app
from apps.worker.services.progress_tracker import ProgressTracker
from apps.worker.services.supabase_admin import get_supabase_admin
import time

@celery_app.task(name='apps.worker.tasks.niche_validate.run', bind=True, max_retries=2)
def run(self, job_id: str, keyword: str):
    supabase = get_supabase_admin()
    tracker = ProgressTracker(supabase, job_id)
    
    try:
        # Stage 1: validation
        tracker.start('validate')
        tracker.tick('validate', 30)
        time.sleep(1)  # mock
        tracker.tick('validate', 80)
        time.sleep(0.5)
        tracker.done('validate')
        
        # Stage 2: cache lookup
        tracker.start('cache_lookup')
        tracker.tick('cache_lookup', 50)
        cache_hit = False  # mock
        tracker.done('cache_lookup')
        
        # Stage 3: result
        result = {
            'keyword': keyword,
            'is_viable': True,
            'total_monthly_views': 8_200_000,
            'google_trends_interest': 67,
            'top_channels_ui': [...],  # 10 channels (mock)
            'top_videos': [...],       # 50 videos (mock)
            'suggested_titles': [
                f'Vì Sao {keyword.title()} Quan Trọng?',
                f'7 Sai Lầm Khi Bắt Đầu {keyword.title()}',
                # ... 3 more
            ],
            'cache_hit': cache_hit,
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Update job result
        supabase.table('jobs').update({
            'status': 'succeeded',
            'progress': 100,
            'result_payload': result,
            'updated_at': 'NOW()',
        }).eq('id', job_id).execute()
        
        # Commit credits
        supabase.rpc('commit_credits', {
            'p_user_id': ...,
            'p_job_id': job_id,
        }).execute()
        
    except Exception as e:
        tracker.fail('validate', str(e))
        supabase.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()
        # Release credits
        supabase.rpc('release_credits', {
            'p_user_id': user_id,
            'p_job_id': job_id,
        }).execute()
        raise
```

---

## 6. Next.js scaffold

### Folder structure
```
apps/web/
  app/
    (auth)/
      login/page.tsx
      register/page.tsx
    (dashboard)/
      layout.tsx
      page.tsx              # Dashboard home
      assistants/
        new/page.tsx        # Create assistant
        [id]/page.tsx       # View assistant
      projects/
        new/page.tsx
        [id]/page.tsx
      jobs/
        [id]/page.tsx       # Realtime progress
    api/                    # BFF route handlers
      auth/...
      proxy to FastAPI
    layout.tsx
    page.tsx                # Landing
  components/
    ui/                     # shadcn
    job-progress.tsx        # Realtime subscribe
    credit-display.tsx
  lib/
    supabase/server.ts
    supabase/client.ts
  middleware.ts             # Auth check
```

### `apps/web/app/(dashboard)/jobs/[id]/page.tsx`
```typescript
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { JobProgressRealtime } from '@/components/job-progress';

export default async function JobPage({ params }: { params: { id: string } }) {
  const supabase = createSupabaseServerClient();
  const { data: job } = await supabase
    .from('jobs')
    .select('*')
    .eq('id', params.id)
    .single();
  
  return (
    <div>
      <h1>Job #{params.id}</h1>
      <pre>{JSON.stringify(job, null, 2)}</pre>
      <JobProgressRealtime jobId={params.id} />
    </div>
  );
}
```

### `apps/web/components/job-progress.tsx`
```typescript
'use client';
import { useEffect, useState } from 'react';
import { createSupabaseClient } from '@/lib/supabase/client';

export function JobProgressRealtime({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  
  useEffect(() => {
    const supabase = createSupabaseClient();
    const channel = supabase
      .channel(`job:${jobId}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'jobs',
        filter: `id=eq.${jobId}`,
      }, (payload) => {
        setProgress(payload.new.progress);
        setStatus(payload.new.status);
      })
      .subscribe();
    
    return () => { supabase.removeChannel(channel); };
  }, [jobId]);
  
  return (
    <div>
      <progress value={progress} max={100} />
      <span>{status} ({progress}%)</span>
    </div>
  );
}
```

---

## 7. Docker Compose

### `docker-compose.yml`
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: appdk
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ['5432:5432']
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ['6379:6379']

  api:
    build: ./apps/api
    command: uvicorn apps.api.main:app --host 0.0.0.0 --reload
    ports: ['8000:8000']
    environment:
      SUPABASE_URL: http://localhost:54321  # dùng supabase local
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    depends_on: [postgres, redis]

  worker:
    build: ./apps/api  # same image
    command: celery -A apps.worker.celery_app worker --loglevel=info --concurrency=4
    environment: { ... giống api ... }
    depends_on: [postgres, redis]

  web:
    build: ./apps/web
    command: pnpm dev
    ports: ['3000:3000']
    environment:
      NEXT_PUBLIC_SUPABASE_URL: http://localhost:54321
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
      FASTAPI_INTERNAL_URL: http://api:8000

volumes:
  pgdata:
```

---

## 8. Acceptance Criteria — Sprint 1 done = ?

| # | Test | Expected |
|---|------|----------|
| AC1.1 | User đăng ký qua `register` page | Tạo user trong `auth.users` + trigger tạo `public.users` với 1000 credits |
| AC1.2 | User đăng nhập qua `login` page | Set session cookie, redirect `/dashboard` |
| AC1.3 | `GET /api/users/me` (với Bearer token) | Return `{credits: 1000, tier: 'free'}` |
| AC1.4 | Click "Validate Niche" → POST `/api/jobs/` | Job created, credits deducted 100, Celery task enqueued |
| AC1.5 | Mở trang `/jobs/{id}` | Thấy progress realtime 0% → 100% trong ~3s (mock) |
| AC1.6 | Job succeeded | Result displayed, credits 900 (100 committed), không refund |
| AC1.7 | Job fail (giả lập bằng cách throw exception) | Credits refund về 1000, error_message hiển thị |
| AC1.8 | Kiểm tra `credit_transactions` table | Có 4 rows: hold(-100), commit(0) / hoặc release(+100) |
| AC1.9 | Realtime qua 2 browser tabs | Cả 2 thấy progress update đồng thời |
| AC1.10 | `docker-compose up` | Tất cả 5 services chạy, app truy cập được ở localhost:3000 |

---

## 9. Out of scope cho Sprint 1

❌ Module 1 (niche validate logic thật — sẽ làm Sprint 3 với real YouTube API)
❌ Script generation (Sprint 4)
❌ OAuth Google (Sprint 7)
❌ Stripe (Sprint 7)
❌ Vision LLM (Sprint 8)
❌ Local ML models (Sprint 5)
❌ Rate limiting (chỉ add basic, full ở Sprint 7)
❌ Admin dashboard (Sprint 7)

---

## 10. Definition of Done

- [ ] Tất cả 10 acceptance criteria pass
- [ ] Coverage ≥ 60% cho `apps/api/` và `apps/worker/`
- [ ] Docker Compose chạy clean với 1 command
- [ ] README root với quickstart instructions
- [ ] Sentry nhận được ít nhất 1 test error
- [ ] Prometheus metrics endpoint exposed ở `/metrics`

---

## 11. Next sprint preview

**Sprint 2 — YouTube Collection Engine (W3-4):**
- YouTube API client với quota rotation
- Cache stampede prevention
- Transcript 3-tier fallback (youtube-transcript-api → Supadata → yt-dlp+Whisper)
- Replace `niche_validate` mock với real API calls
- File: `02_sprint2_youtube_collection.md`
