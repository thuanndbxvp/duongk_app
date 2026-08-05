# PRD v2 — YouTube AI SaaS
> Tài liệu Đặc tả Sản phẩm & Kiến trúc Kỹ thuật
> Tích hợp: `kientruc.md` (v1) + `kientruc_bug_tieman.md` (12 điểm mờ) + `plan1.md` (YouTube quota) + `plan2.md` (Market Research flow + cache) + `plan3.md` (Anti-AI-Slop RAG + Unsplash) + `DNA_plan.md` (14 bước chống AI Slop) + `ana_plan1.md` + `ana_plan2.md` (OverseerOS-style Deep Channel Analysis — 13 outputs)
> Sẵn sàng đưa vào Cursor / Cline / GitHub Copilot để code generation.

---

## 0. MỤC LỤC

1. [Tech Stack đã chốt](#1-tech-stack-đã-chốt)
2. [Monorepo & Kiến trúc tổng thể](#2-monorepo--kiến-trúc-tổng-thể)
3. [Database Schema đầy đủ](#3-database-schema-đầy-đủ)
4. [RLS Policy Template](#4-rls-policy-template)
5. [API Endpoints & Contract (Pydantic ↔ Zod)](#5-api-endpoints--contract-pydantic--zod)
6. [Chiến lược Auth & BFF Pattern](#6-chiến-lược-auth--bff-pattern)
7. [Realtime & Job Tracking](#7-realtime--job-tracking)
8. [Module 0 (Lite) — User, Credit, Tier](#8-module-0-lite--user-credit-tier)
9. [Module 1 — Discovery & Validation](#9-module-1--discovery--validation)
10. [Module 2 — Content Engine (3 Phase)](#10-module-2--content-engine-3-phase)
10a. **🆕 [State Machine 14 Bước & Chained LLM Calls](#10a--state-machine-14-bước--chained-llm-calls-mới)**
10b. **🆕 [Outlier Strength & Video Viral Selection](#10b--outlier-strength--video-viral-selection-mới)**
10c. **🆕 [Critical Visual Rule & Anti-AI-Slop](#10c--critical-visual-rule--anti-ai-slop-mới)**
10d. **🆕 [Channel Blueprint — 6 Power Features](#10d--channel-blueprint--6-power-features-mới)**
10e. **🆕 [Deep Channel Analysis — OverseerOS-style Report](#10e--deep-channel-analysis--overseeros-style-report-mới)**
11. [Prompt Templates (Style DNA / Script / Scene Breakdown)](#11-prompt-templates)
12. [JSON Schema chuẩn cho `scenes_data` & `style_dna_profile`](#12-json-schema-chuẩn)
13. [Credit Billing — Hold-Commit-Release](#13-credit-billing--hold-commit-release)
14. [Rate Limiting & Abuse Protection](#14-rate-limiting--abuse-protection)
15. [Error Handling & Retry Policy](#15-error-handling--retry-policy)
16. [Logging & Cost Tracking](#16-logging--cost-tracking)
17. [Bảo mật API Key](#17-bảo-mật-api-key)
18. [Phase Roadmap đã chốt](#18-phase-roadmap-đã-chốt)
19. [Prompt đưa cho AI Coding](#19-prompt-đưa-cho-ai-coding)

---

## 1. Tech Stack đã chốt

| Lớp | Công nghệ | Ghi chú |
|-----|-----------|---------|
| Frontend | **Next.js 14 (App Router)** + React + TailwindCSS + Shadcn UI | Server Components cho SEO, Client Components cho UI tương tác |
| BFF | **Next.js Route Handlers** (`/app/api/*/route.ts`) | Proxy tới FastAPI, giữ Supabase JWT |
| Backend | **Python 3.11 + FastAPI** + Pydantic v2 + SQLAlchemy 2 | Async, OpenAPI auto-gen |
| Worker | **Celery 5 + Redis 7** | 2 queue riêng: `ai_queue` (LLM) và `fetch_queue` (Pexels) |
| DB | **Supabase (PostgreSQL 15)** + Supabase Auth + Supabase Realtime + Supabase Storage | |
| AI | **OpenAI GPT-4o** (chính), fallback Gemini 1.5 Pro · **gpt-image-1** (thumbnail gen §10d.6) · **text-embedding-3-small** (RAG §10c.7) | Trừ qua env, route qua Worker |
| Footage | **Pexels API** (video) + **Pixabay API** (video/image) + 🆕 **Unsplash API** (ảnh tĩnh chất lượng cao, fallback cuối cho image) | Unsplash Demo: 50 req/hr, Prod: 5000 req/hr |
| YouTube | **YouTube Data API v3** — dùng luồng `channels.list → playlistItems.list → videos.list` (3 quota/kênh) | Cache Redis 24h |
| Transcript | **`youtube-transcript-api`** (ưu tiên, free) → fallback **yt-dlp + Whisper** nếu không có caption | Whisper chỉ chạy ở Worker, không bao giờ ở Web |
| Deploy | Frontend: Vercel · Backend: Fly.io hoặc Railway · Worker: cùng Fly.io · Redis: Upstash · DB: Supabase Cloud | |

---

## 2. Monorepo & Kiến trúc tổng thể

### 2.1. Cấu trúc thư mục (Turborepo + pnpm workspaces)

```
youtube-ai-saas/
├── apps/
│   ├── web/                  # Next.js 14 (App Router)
│   │   ├── app/
│   │   │   ├── (marketing)/  # Landing, pricing
│   │   │   ├── (auth)/       # login, signup
│   │   │   ├── (app)/        # Dashboard: /research, /assistants, /projects
│   │   │   └── api/          # BFF route handlers
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   ├── api/                  # FastAPI
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── users.py
│   │   │   │   ├── research.py
│   │   │   │   ├── assistants.py
│   │   │   │   └── projects.py
│   │   │   ├── deps/         # auth, credit check, rate limit
│   │   │   ├── schemas/      # Pydantic models
│   │   │   └── services/     # business logic (gọi Celery, DB)
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── worker/               # Celery
│       ├── celery_app.py
│       ├── tasks/
│       │   ├── research.py
│       │   ├── style_dna.py
│       │   ├── script_gen.py
│       │   └── scene_breakdown.py
│       └── pyproject.toml
├── packages/
│   ├── shared-types/         # Pydantic + Zod schema mirror
│   │   ├── py/               # Python Pydantic (dùng cho FastAPI)
│   │   ├── ts/               # TypeScript Zod (dùng cho Next.js)
│   │   └── schemas/
│   │       ├── scene.py
│   │       ├── style_dna.py
│   │       └── ...
│   └── ui/                   # Component dùng chung (Button, Card, Modal)
├── supabase/
│   ├── migrations/           # *.sql migration files
│   ├── policies/             # *.sql RLS policy files
│   └── seed.sql
├── .env.example
├── turbo.json
├── pnpm-workspace.yaml
└── README.md
```

### 2.2. Sơ đồ luồng request

```
[Browser]
   │
   │ (1) Gọi kèm Supabase JWT trong cookie/Authorization header
   ▼
[Next.js Route Handler — BFF]
   │ (2) Verify JWT bằng @supabase/ssr (server-side)
   │ (3) Forward sang FastAPI + service-role header (internal secret)
   ▼
[FastAPI]
   │ (4) Verify internal secret + extract user_id
   │ (5) Check credit (HOLD) + check rate limit
   │ (6) Enqueue Celery task, trả job_id ngay
   ▼
[Celery Worker]
   │ (7) Gọi LLM / YouTube / Pexels
   │ (8) Ghi DB + cập nhật job status
   │ (9) COMMIT credit hoặc RELEASE nếu fail
   ▼
[Supabase Realtime] ──push──▶ [Next.js Client subscribe] ──render──▶ UI
```

---

## 3. Database Schema đầy đủ

> File: `supabase/migrations/0001_init.sql`

```sql
-- ============================================================
-- EXTENSIONS
-- ============================================================
create extension if not exists "uuid-ossp";
create extension if not exists "pg_trgm"; -- dùng cho search keyword

-- ============================================================
-- USERS (extend Supabase auth.users)
-- ============================================================
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  display_name text,
  tier text not null default 'internal_test'
    check (tier in ('internal_test', 'free', 'pro', 'agency')),
  credits integer not null default 1000, -- mock lớn cho giai đoạn dev
  credits_held integer not null default 0, -- credit đang bị hold bởi job pending
  max_assistants integer not null default 3,
  max_concurrent_jobs integer not null default 2,
  byok_openai_key_encrypted text, -- optional BYOK, đã mã hoá
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Auto tạo user row khi đăng ký Supabase Auth
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- PLANS (tham chiếu giá, không hard-code trong code)
-- ============================================================
create table public.plans (
  id text primary key, -- 'free', 'pro', 'agency'
  display_name text not null,
  monthly_price_usd numeric(10,2) not null,
  credits_per_month integer not null,
  max_assistants integer not null,
  max_concurrent_jobs integer not null,
  features jsonb not null default '{}',
  created_at timestamptz not null default now()
);

insert into public.plans values
  ('free', 'Free', 0, 50, 1, 1, '{}'),
  ('pro', 'Pro', 19, 1000, 10, 3, '{"realtime": true}'),
  ('agency', 'Agency', 99, 10000, 50, 10, '{"realtime": true, "priority_queue": true}');

-- ============================================================
-- CREDIT TRANSACTIONS (audit log mọi lần cộng/trừ)
-- ============================================================
create type credit_tx_type as enum ('hold', 'commit', 'release', 'topup', 'refund', 'bonus');

create table public.credit_transactions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  type credit_tx_type not null,
  amount integer not null, -- dương = cộng, âm = trừ
  balance_after integer not null,
  held_after integer not null,
  job_id uuid, -- liên kết job (nếu có)
  reason text not null,
  metadata jsonb default '{}',
  created_at timestamptz not null default now()
);

create index idx_credit_tx_user_created on public.credit_transactions(user_id, created_at desc);

-- ============================================================
-- JOBS (track mọi Celery task async)
-- ============================================================
create type job_status as enum ('pending', 'running', 'completed', 'failed', 'cancelled');

create table public.jobs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  type text not null check (type in ('market_research', 'style_dna_extract', 'script_generate', 'scene_breakdown')),
  status job_status not null default 'pending',
  celery_task_id text unique,
  progress smallint not null default 0 check (progress between 0 and 100),
  input jsonb not null,
  result jsonb,
  error text,
  credits_held integer not null default 0,
  credits_charged integer not null default 0,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index idx_jobs_user_status on public.jobs(user_id, status);
create index idx_jobs_celery on public.jobs(celery_task_id);

-- Realtime: enable cho jobs
alter publication supabase_realtime add table public.jobs;

-- ============================================================
-- API USAGE LOGS (log chi phí thực tế mỗi lần gọi API)
-- ============================================================
create table public.api_usage_logs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete set null,
  job_id uuid references public.jobs(id) on delete set null,
  provider text not null check (provider in ('openai', 'gemini', 'youtube', 'pexels', 'pixabay', 'unsplash', 'whisper', 'yt_dlp')),
  model text,
  endpoint text,
  input_tokens integer default 0,
  output_tokens integer default 0,
  duration_ms integer,
  cost_usd numeric(10,6) not null default 0,
  status text not null,
  error text,
  metadata jsonb default '{}',
  created_at timestamptz not null default now()
);

create index idx_api_usage_user_created on public.api_usage_logs(user_id, created_at desc);
create index idx_api_usage_job on public.api_usage_logs(job_id);

-- ============================================================
-- CHANNEL ASSISTANTS (Style DNA)
-- ============================================================
create table public.channel_assistants (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  name text not null,
  seed_channel_id text not null,
  seed_channel_url text not null,
  style_dna_profile jsonb,                 -- xem schema §12.1 (v1, flat)
  style_dna_profile_v2 jsonb,             -- xem schema §12.5 (v2, 3-layer) — mới
  xray_profile jsonb,                     -- xem schema §12.3 — mới từ DNA_plan
  thumbnail_profile jsonb,                -- xem schema §12.4 — mới từ DNA_plan
  outlier_videos jsonb,                   -- xem §10b — mới
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index idx_assistants_user on public.channel_assistants(user_id);

-- ============================================================
-- MARKET RESEARCH (Module 1)
-- ============================================================
create type research_status as enum ('pending', 'running', 'completed', 'failed');

create table public.market_research (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  keyword text not null,
  status research_status not null default 'pending',
  total_monthly_views bigint,
  viable_threshold bigint not null default 5000000,
  is_viable boolean,
  top_competitors jsonb, -- array: [{channel_id, title, subs, top_video_id, top_video_views}]
  suggested_titles jsonb, -- array of strings
  job_id uuid references public.jobs(id),
  created_at timestamptz not null default now()
);

create index idx_research_user_keyword on public.market_research(user_id, keyword);

-- ============================================================
-- CONTENT PROJECTS (Module 2)
-- ============================================================
create type project_status as enum ('draft', 'generating_script', 'script_ready', 'breaking_scenes', 'completed', 'failed'));

create table public.content_projects (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  assistant_id uuid references public.channel_assistants(id) on delete set null,
  topic text not null,
  status project_status not null default 'draft',
  raw_script text,
  scenes_data jsonb, -- xem schema ở §12
  current_job_id uuid references public.jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_projects_user_status on public.content_projects(user_id, status);

alter publication supabase_realtime add table public.content_projects;
```

---

## 4. RLS Policy Template

> File: `supabase/policies/0001_rls.sql`

```sql
-- Helper: lấy user_id hiện tại
create or replace function public.current_user_id() returns uuid
language sql stable as $$
  select auth.uid()
$$;

-- Bật RLS cho tất cả bảng
alter table public.users enable row level security;
alter table public.channel_assistants enable row level security;
alter table public.market_research enable row level security;
alter table public.content_projects enable row level security;
alter table public.jobs enable row level security;
alter table public.credit_transactions enable row level security;
alter table public.api_usage_logs enable row level security;
alter table public.plans enable row level security;

-- Plans: ai cũng đọc được (public pricing)
create policy "plans_public_read" on public.plans
  for select using (true);

-- Users: chỉ thấy chính mình
create policy "users_self_select" on public.users
  for select using (id = public.current_user_id());

create policy "users_self_update" on public.users
  for update using (id = public.current_user_id());

-- Channel assistants
create policy "assistants_owner_all" on public.channel_assistants
  for all using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

-- Market research
create policy "research_owner_all" on public.market_research
  for all using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

-- Content projects
create policy "projects_owner_all" on public.content_projects
  for all using (user_id = public.current_user_id())
  with check (user_id = public.current_user_id());

-- Jobs: chỉ owner
create policy "jobs_owner_select" on public.jobs
  for select using (user_id = public.current_user_id());

-- Credit transactions: chỉ owner
create policy "credit_tx_owner_select" on public.credit_transactions
  for select using (user_id = public.current_user_id());

-- API usage logs: chỉ owner
create policy "api_usage_owner_select" on public.api_usage_logs
  for select using (user_id = public.current_user_id());

-- ⚠️ Service role key (dùng trong FastAPI Worker) bypass RLS — KHÔNG expose cho client.
```

---

## 5. API Endpoints & Contract (Pydantic ↔ Zod)

> Base URL (BFF): `https://app.example.com/api`
> Base URL (FastAPI trực tiếp — internal): `https://api.internal.example.com`

### 5.1. Auth & Users

```
GET    /api/users/me                    → UserPublic
GET    /api/users/me/credits            → { available, held, transactions[] }
GET    /api/users/me/jobs?status=...    → JobPublic[]
```

### 5.2. Module 1 — Market Research

```
POST   /api/research/validate
       body: { keyword: string, region?: string, language?: string }
       → 202 { job_id, research_id }

GET    /api/research/{research_id}
       → MarketResearchPublic

GET    /api/research?limit=20
       → MarketResearchPublic[] (lịch sử)
```

### 5.3. Module 2 — Assistants & Projects

```
POST   /api/assistants
       body: { name: string, seed_channel_url: string }
       → 202 { job_id, assistant_id }

GET    /api/assistants                  → ChannelAssistantPublic[]
GET    /api/assistants/{id}             → ChannelAssistantPublic (đầy đủ style_dna_profile)

POST   /api/projects
       body: { topic: string, assistant_id: uuid }
       → 202 { job_id, project_id }

GET    /api/projects/{id}               → ContentProjectPublic (đầy đủ scenes_data)
PATCH  /api/projects/{id}/script        body: { raw_script: string }
PATCH  /api/projects/{id}/scenes/{scene_id}/asset
       body: { download_url: string, asset_type: 'video'|'image' }

POST   /api/projects/{id}/break-scenes  (chạy Phase 2.3 manually)
       → 202 { job_id }
```

### 5.4. Pydantic schema (file `packages/shared-types/py/schemas.py`)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID

# ---- Style DNA (v1 flat — giữ nguyên cho backward compat) ----
class StyleDNAProfile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hook_patterns: list[str]
    vocabulary_tier: Literal['casual', 'conversational', 'formal', 'academic']
    avg_sentence_length: int = Field(ge=3, le=50)
    pacing: Literal['slow', 'medium', 'fast']
    signature_phrases: list[str]
    rhetorical_devices: list[str]
    tone_keywords: list[str]
    example_hooks: list[str]

# ---- 🆕 Style DNA v2 (3-layer) ----
class WritingStyleLayer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hook_patterns: list[str]
    vocabulary_tier: Literal['casual', 'conversational', 'formal', 'academic']
    avg_sentence_length: int = Field(ge=3, le=50)
    pacing: Literal['slow', 'medium', 'fast']
    signature_phrases: list[str]
    rhetorical_devices: list[str]
    tone_keywords: list[str]
    example_hooks: list[str]

class StructureLayer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    typical_intro_seconds: int = Field(ge=5, le=120)
    typical_outro_seconds: int = Field(ge=5, le=120)
    sections_per_video: int = Field(ge=1, le=20)
    section_templates: list[str]
    transition_phrases: list[str]
    curiosity_gaps_per_minute: float = Field(ge=0, le=5)

class EmotionPoint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    phase: str
    emotion: str
    intensity: int = Field(ge=1, le=10)

class RetentionLayer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    emotion_curve: list[EmotionPoint]
    open_loop_count_avg: int = Field(ge=0)
    pattern_interrupt_cadence_sec: int = Field(ge=10, le=600)
    cta_type: Literal['subscribe', 'comment', 'next_video', 'lead_magnet', 'custom']
    cta_position: Literal['mid_video', 'outro', 'both']

class StyleDNAProfileV2(BaseModel):
    """3-layer Style DNA từ DNA_plan.md."""
    model_config = ConfigDict(extra='forbid')
    writing_style: WritingStyleLayer
    structure: StructureLayer
    retention: RetentionLayer

# ---- 🆕 X-Ray ----
class AudiencePersona(BaseModel):
    model_config = ConfigDict(extra='forbid')
    age_range: str
    primary_interest: str
    pain_points: list[str]
    aspirations: list[str]

class EmotionalPacingPoint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    phase: Literal['hook', 'setup', 'buildup', 'payoff', 'cta', 'transition']
    emotion: str
    intensity: int = Field(ge=1, le=10)

class ChannelXRay(BaseModel):
    model_config = ConfigDict(extra='forbid')
    niche: str
    audience_persona: AudiencePersona
    emotional_pacing_curve: list[EmotionalPacingPoint]
    retention_techniques: list[str]
    thumbnail_patterns: list[str]
    title_formulas: list[str]

# ---- 🆕 Thumbnail Profile ----
class TextOverlayStyle(BaseModel):
    model_config = ConfigDict(extra='forbid')
    typical_word_count: int = Field(ge=0, le=10)
    font_style: str
    common_words: list[str] = []

class FacePatterns(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expression_intensity: Literal['low', 'medium', 'high', 'extreme']
    eye_contact_with_camera: bool
    common_gaze_direction: str

class ThumbnailProfile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    color_palette: list[str]  # ["#FF0050", "#00FFAA", ...]
    dominant_layouts: list[str]
    text_overlay_style: TextOverlayStyle
    face_patterns: Optional[FacePatterns] = None
    background_patterns: list[str] = []
    clickbait_score_avg: int = Field(ge=1, le=10)
    emotional_triggers: list[str]
    reusable_template: str = Field(min_length=50)

# ---- 🆕 Outlier Video ----
class OutlierVideo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    video_id: str
    title: str
    views: int
    published_at: datetime
    outlier_score: float
    thumbnail_url: Optional[str] = None
    transcript: Optional[str] = None

# ---- Scene ----
class SceneAsset(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['video', 'image']
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_sec: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    provider: Optional[Literal['pexels', 'pixabay', 'unsplash', 'ai_generated']] = None
    license: Optional[str] = None
    fetched_at: Optional[datetime] = None

class Scene(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scene_id: int = Field(ge=1)
    text: str = Field(min_length=1)
    estimated_duration: float = Field(gt=0)
    visual_context: str
    search_keyword: str
    search_keywords_alt: list[str] = []  # fallback
    asset_type_needed: Literal['video', 'image']
    asset: Optional[SceneAsset] = None
    asset_status: Literal['pending', 'fetched', 'no_result', 'fallback_image'] = 'pending'

# ---- Channel Assistant ----
class ChannelAssistantPublic(BaseModel):
    id: UUID
    name: str
    seed_channel_url: str
    style_dna_profile: Optional[StyleDNAProfile] = None
    style_dna_profile_v2: Optional[StyleDNAProfileV2] = None
    xray_profile: Optional[ChannelXRay] = None
    thumbnail_profile: Optional[ThumbnailProfile] = None
    outlier_videos: Optional[list[OutlierVideo]] = None
    created_at: datetime

# ---- Market Research ----
class TopCompetitor(BaseModel):
    channel_id: str
    title: str
    subs: int
    top_video_id: Optional[str]
    top_video_views: Optional[int]

class MarketResearchPublic(BaseModel):
    id: UUID
    keyword: str
    status: Literal['pending', 'running', 'completed', 'failed']
    total_monthly_views: Optional[int]
    viable_threshold: int
    is_viable: Optional[bool]
    top_competitors: Optional[list[TopCompetitor]]
    suggested_titles: Optional[list[str]]
    created_at: datetime

# ---- Content Project ----
class ContentProjectPublic(BaseModel):
    id: UUID
    assistant_id: Optional[UUID]
    topic: str
    status: Literal['draft', 'generating_script', 'script_ready', 'breaking_scenes', 'completed', 'failed']
    raw_script: Optional[str]
    scenes_data: Optional[list[Scene]]
    created_at: datetime
    updated_at: datetime

# ---- Job ----
class JobPublic(BaseModel):
    id: UUID
    type: Literal['market_research', 'style_dna_extract', 'script_generate', 'scene_breakdown']
    status: Literal['pending', 'running', 'completed', 'failed', 'cancelled']
    progress: int
    error: Optional[str]
    result: Optional[dict]
    created_at: datetime
    finished_at: Optional[datetime]

# ---- User ----
class UserPublic(BaseModel):
    id: UUID
    email: str
    tier: Literal['internal_test', 'free', 'pro', 'agency']
    credits: int
    credits_held: int
    max_assistants: int
```

### 5.5. Zod mirror (file `packages/shared-types/ts/schemas.ts`)

> Cùng tên field, cùng validation rule. Auto-generate bằng `py2zod` hoặc maintain song song với CI check.

---

## 6. Chiến lược Auth & BFF Pattern

**Chốt:** **BFF pattern** (Browser → Next.js Route Handler → FastAPI).

- Browser **KHÔNG bao giờ** gọi trực tiếp FastAPI.
- Next.js giữ Supabase session (cookie httpOnly), verify bằng `@supabase/ssr`.
- Next.js forward request sang FastAPI kèm header `X-Internal-Secret` (random 256-bit) + `X-User-Id` (lấy từ session đã verify).
- FastAPI **tin tưởng tuyệt đối** `X-User-Id` (vì chỉ chấp nhận khi có `X-Internal-Secret` đúng → không expose ra public).
- Mọi query DB từ FastAPI dùng **Supabase Service Role Key** để bypass RLS (vì đã tự filter theo `user_id` từ header).

```typescript
// apps/web/app/api/research/validate/route.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const cookieStore = cookies();
  const supabase = createServerClient(/* ... */);
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const body = await req.json();
  const apiRes = await fetch(`${process.env.FASTAPI_URL}/research/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Secret': process.env.INTERNAL_SECRET!,
      'X-User-Id': user.id,
    },
    body: JSON.stringify(body),
  });
  return NextResponse.json(await apiRes.json(), { status: apiRes.status });
}
```

```python
# apps/api/app/deps/auth.py
from fastapi import Header, HTTPException, Depends
import hmac

async def get_current_user(
    x_internal_secret: str = Header(...),
    x_user_id: str = Header(...),
) -> str:
    if not hmac.compare_digest(x_internal_secret, os.environ['INTERNAL_SECRET']):
        raise HTTPException(status_code=401, detail='invalid_internal_secret')
    return x_user_id
```

---

## 7. Realtime & Job Tracking

**Chốt:** **Supabase Realtime** (không tự build WebSocket).

### 7.1. Client subscribe (Next.js)

```typescript
'use client';
import { useEffect, useState } from 'react';
import { createBrowserClient } from '@supabase/ssr';

export function useJobStatus(jobId: string) {
  const [job, setJob] = useState<JobPublic | null>(null);
  const supabase = createBrowserClient(/* ... */);

  useEffect(() => {
    const channel = supabase
      .channel(`job:${jobId}`)
      .on('postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'jobs', filter: `id=eq.${jobId}` },
        (payload) => setJob(payload.new as JobPublic)
      )
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [jobId]);

  return job;
}
```

### 7.2. Worker update progress

```python
# apps/worker/tasks/scene_breakdown.py
from celery import shared_task
from supabase import create_client

@shared_task(bind=True, max_retries=2)
def breakdown_scenes(self, project_id: str, user_id: str):
    sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
    job_id = self.request.id

    try:
        sb.table('jobs').update({'status': 'running', 'progress': 10}).eq('id', job_id).execute()
        # ... gọi LLM, update progress 30, 60 ...
        sb.table('content_projects').update({'scenes_data': scenes}).eq('id', project_id).execute()
        sb.table('jobs').update({'status': 'completed', 'progress': 100, 'finished_at': 'now()'}).eq('id', job_id).execute()
    except Exception as e:
        sb.table('jobs').update({'status': 'failed', 'error': str(e)}).eq('id', job_id).execute()
        raise
```

### 7.3. Polling fallback

- Mọi endpoint `GET /api/jobs/{id}` và `GET /api/projects/{id}` đều có sẵn.
- Nếu client không subscribe realtime được (network issue) → dùng polling 2s.

---

## 8. Module 0 (Lite) — User, Credit, Tier

### 8.1. Phase 1 scope

| Có ngay Phase 1 | Đẩy sang Phase 2 |
|------------------|--------------------|
| Bảng `users` (auth + credits mock 1000) | UI Profile đầy đủ, đổi mật khẩu |
| Supabase Auth email/password | OAuth Google/Facebook, magic link |
| RLS policy đầy đủ cho mọi bảng | Onboarding tour, referral |
| Middleware trừ credit (Hold-Commit-Release) | Stripe billing portal |
| Bảng `credit_transactions` | Auto top-up khi hết |
| Hard-coded 1 tier `internal_test` | Multi-tier limits + UI chọn gói |
| Endpoint `GET /users/me`, `GET /users/me/credits` | `/billing/portal` |

### 8.2. Credit rules (Phase 1)

| Action | Credits (Phase 1) | Ghi chú |
|--------|-------------------|---------|
| `market_research` (Module 1) | 5 | Fixed |
| `style_dna_extract` (Phase 2.1) | 10 | LLM gọi nhiều transcript |
| `script_generate` (Phase 2.2) | 20 | Fixed per script |
| `scene_breakdown` (Phase 2.3) | 1/scene | Ví dụ 10 cảnh = 10 credits |

### 8.3. Tier matrix

| Tier | credits/mo | max_assistants | concurrent_jobs | byok |
|------|------------|----------------|------------------|------|
| `internal_test` | 1000 (mock) | 10 | 5 | optional |
| `free` | 50 | 1 | 1 | no |
| `pro` | 1000 | 10 | 3 | optional |
| `agency` | 10000 | 50 | 10 | optional |

---

## 9. Module 1 — Discovery & Validation

> Tích hợp từ `plan2.md` — flow 4 bước chuẩn cho Market Research.

### 9.1. Input
```ts
{ keyword: string, region?: 'US'|'VN'|... = 'US', language?: string = 'en' }
```

### 9.2. Ngưỡng Validation

- **Viable threshold:** `5,000,000` views / 30 ngày (lưu trong `market_research.viable_threshold`, user có thể override nhưng mặc định 5M).
- Nếu `total_monthly_views < viable_threshold` → trả về `is_viable=false` + message warning, **KHÔNG** chạy tiếp Bước 3 và Bước 4.
- Threshold có thể config per-niche trong `plans` table (Phase 2).

### 9.3. Workflow 4 bước (Celery Worker)

```
BƯỚC 1 — Search Top 50 video (30 ngày gần nhất)
─────────────────────────────────────────────────
API: search.list(q=keyword, type=video, publishedAfter=now-30d, maxResults=50)
Quota: 100 units (search.list rất đắt!)
Chi phí: Nếu keyword tiếng Việt → dịch sang EN qua GPT trước khi search
         (ghi log cost_openai_translate)

Output: 50 video_ids, 50 channel_ids (unique ~30-50 kênh)

BƯỚC 2 — Tính tổng View tháng (Validation Gate)
─────────────────────────────────────────────────
API: videos.list(id=id1,id2,...id50, part=statistics,snippet)  ← 1 request duy nhất!
Quota: 1 unit

Tính:  total_monthly_views = sum(viewCount)
       Nếu < 5,000,000 → RETURN sớm với is_viable=false

Lưu:   language filter check (defaultLanguage / defaultAudioLanguage)
       để đảm bản tính trên thị trường quốc tế (EN mặc định)

BƯỚC 3 — Lấy thông tin các Kênh unique
─────────────────────────────────────────────────
API: channels.list(id=cid1,cid2,...cid50, part=statistics,snippet)  ← 1 request!
Quota: 1 unit (max 50 channel_ids / call)

Lấy:   subscriberCount, viewCount, customUrl
⚠️ Hidden subs: Một số kênh ẩn sub → try/except set default = 0
   (Xem code mẫu §9.5)

BƯỚC 4 — Sort theo Sub & trả Top 10
─────────────────────────────────────────────────
Sort channels_data theo subscriberCount DESC
→ top_competitors (lưu Top 10 vào market_research.top_competitors)

SAU ĐÓ (tuỳ chọn, nếu user muốn Top 100):
- Với mỗi kênh trong Top 10: dùng luồng 3 quota của plan1.md
  (channels.list → playlistItems.list → videos.list) → tính views_30d per channel
- Sort lại theo views_30d → Top 100 channels
- Cache Redis 24h key="yt:channel:{channel_id}:stats"

BƯỚC 5 — Sinh 5 title suggestions
─────────────────────────────────────────────────
- Lấy titles của 100 video top đầu
- Prompt GPT với template §9.4 → 5 suggested_titles
- Ghi api_usage_logs (input_tokens, output_tokens, cost_usd)

BƯỚC 6 — Cập nhật DB
─────────────────────────────────────────────────
- market_research row → status=completed
- credit_transactions → commit (nếu hold thành công)
```

### 9.4. Output Schema

```ts
{
  id, keyword,
  status: 'completed',
  total_monthly_views: 8_420_000,
  viable_threshold: 5_000_000,
  is_viable: true,
  top_competitors: [
    {channel_id, title, subs, total_views, custom_url, top_video_id, top_video_views},
    ...10 items (Phase 1) hoặc 100 items (nếu user nâng cấp)
  ],
  suggested_titles: ["...", ...5 items]
}
```

### 9.5. Code mẫu Python (file `apps/worker/tasks/research.py`)

```python
from datetime import datetime, timedelta, timezone
import logging

from googleapiclient.discovery import build
from ..services.cache import redis_client
from ..services.llm import call_llm, log_api_call

logger = logging.getLogger(__name__)
youtube = build('youtube', 'v3', developerKey=os.environ['YOUTUBE_API_KEY'])

CACHE_TTL_SECONDS = 24 * 3600  # 24 giờ (theo plan2.md; một số trường hợp 72h)


def safe_int(value, default=0):
    """Xử lý hidden subscriber / missing field — plan2.md yêu cầu rõ."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def validate_and_find_top_channels(keyword: str, language: str = 'en') -> dict:
    """Flow 4 bước từ plan2.md."""

    # ===== BƯỚC 1: Search Top 50 video trong 30 ngày qua =====
    one_month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    search_response = youtube.search().list(
        q=keyword,
        type='video',
        part='snippet',
        publishedAfter=one_month_ago,
        maxResults=50,
        relevanceLanguage=language,
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
    if not video_ids:
        return {'is_viable': False, 'total_monthly_views': 0,
                'message': 'Không tìm thấy video nào trong 30 ngày qua.'}

    # ===== BƯỚC 2: Tính tổng view tháng =====
    videos_response = youtube.videos().list(
        id=','.join(video_ids),
        part='statistics,snippet',
    ).execute()

    total_monthly_views = 0
    channel_ids = set()
    for item in videos_response.get('items', []):
        total_monthly_views += safe_int(item['statistics'].get('viewCount'))
        channel_ids.add(item['snippet']['channelId'])

    # ===== Validation Gate =====
    VIABLE_THRESHOLD = 5_000_000
    if total_monthly_views < VIABLE_THRESHOLD:
        return {
            'is_viable': False,
            'total_monthly_views': total_monthly_views,
            'viable_threshold': VIABLE_THRESHOLD,
            'message': f'Chủ đề chưa đủ độ hot (< {VIABLE_THRESHOLD/1_000_000}M view/tháng).',
        }

    # ===== BƯỚC 3: Lấy thông tin các kênh unique =====
    channels_response = youtube.channels().list(
        id=','.join(list(channel_ids)[:50]),  # max 50 ids / call
        part='statistics,snippet',
    ).execute()

    channels_data = []
    for item in channels_response.get('items', []):
        channels_data.append({
            'channel_id':   item['id'],
            'title':        item['snippet']['title'],
            'subscribers':  safe_int(item['statistics'].get('subscriberCount')),  # ← hidden subs
            'total_views':  safe_int(item['statistics'].get('viewCount')),
            'custom_url':   item['snippet'].get('customUrl', ''),
        })

    # ===== BƯỚC 4: Sort theo Sub & Top 10 =====
    top_10 = sorted(channels_data, key=lambda x: x['subscribers'], reverse=True)[:10]

    return {
        'is_viable': True,
        'total_monthly_views': total_monthly_views,
        'viable_threshold': VIABLE_THRESHOLD,
        'top_competitors': top_10,
    }
```

### 9.6. Cache Strategy (Redis) — từ plan2.md

```
Key:    "research:keyword:{language}:{keyword_normalized}"
TTL:    24 giờ (mặc định) — một số niche "evergreen" dùng 72 giờ
Value:  toàn bộ output của validate_and_find_top_channels()

Cache hit → trả về ngay (~100ms), KHÔNG tốn quota
Cache miss → gọi YouTube + LLM như thường

Invalidation:
- User bấm nút "Refresh" trên UI → DEL key trước khi chạy
- Admin có thể FLUSHDB theo pattern qua admin endpoint
```

```python
def research_with_cache(keyword: str, language: str, force_refresh: bool = False) -> dict:
    cache_key = f"research:keyword:{language}:{keyword.lower().strip()}"

    if not force_refresh:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    result = validate_and_find_top_channels(keyword, language)
    if result['is_viable']:
        redis_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(result))
    return result
```

### 9.7. Prompt sinh titles (file `apps/worker/prompts/research_titles.py`)

```python
RESEARCH_TITLE_PROMPT = """You are a YouTube title expert.
Given 100 successful video titles in the "{niche}" niche (avg views: {avg_views:,}),
generate 5 NEW titles that:
- Are in {language}
- Maximum 70 characters
- Use proven patterns: numbers, curiosity gaps, emotion
- Are NOT copies of any existing title

Return JSON: {{"titles": ["...", "...", "...", "...", "..."]}}

Top 100 titles (truncated):
{titles_sample}
"""
```

---

## 10. Module 2 — Content Engine (3 Phase)

### 10.1. Phase 2.1 — Style DNA Extraction

**Input:** `{ name, seed_channel_url }`

**Workflow:**
```
1. channels.list?forUsername hoặc forHandle → channel_id, uploads_playlist_id
2. playlistItems.list → 50 video mới nhất
3. videos.list → sort by viewCount → lấy top 5 video viral (≥30 ngày tuổi)
4. Với mỗi video viral:
   a. youtube-transcript-api.get_transcript(video_id)
      → nếu fail (no caption) → fallback yt-dlp + Whisper API (ghi log cost)
   b. Lưu transcripts vào list

5. Prompt GPT với 5 transcript + JSON schema output:
   → style_dna_profile (xem §12)

6. Lưu vào channel_assistants.style_dna_profile (JSONB)
```

### 10.2. Phase 2.2 — Script Generation

**Input:** `{ topic, assistant_id }`

**Workflow:**
```
1. Load style_dna_profile từ assistant_id
2. Prompt GPT với topic + style DNA + format rules
   - target_duration: mặc định 8 phút
   - include hook (30s đầu) + body + CTA
3. Output: raw_script (text)
4. Lưu content_projects.raw_script, status=script_ready
```

> User có thể `PATCH /projects/{id}/script` để edit trước khi chạy Phase 2.3.

### 10.3. Phase 2.3 — Scene Breakdown & Asset Fetching ⭐

**Input:** `raw_script` (đã được user confirm)

**Workflow:**

**Bước A — Scene Breakdown (LLM):**
```
1. Prompt GPT với raw_script + style DNA + scene rules:
   - Mỗi scene 4-8 giây
   - Mỗi scene phải self-contained (visual_context rõ ràng)
   - Sinh search_keyword EN (ưu tiên) + search_keywords_alt (fallback)
   - Sinh asset_type_needed: 'video' | 'image'
2. Validate JSON output (Pydantic Scene[]) → nếu fail → retry 1 lần với stricter prompt
3. Tính estimated_duration = len(text) / 2.5 (tốc độ đọc 150 wpm = 2.5 từ/giây)
4. Update content_projects.scenes_data, status=breaking_scenes
5. Update job progress: 50%
```

**Bước B — Asset Fetching (Worker vòng lặp) — Fallback chain 4 tầng:**
```
Với mỗi scene trong scenes_data:
  1. Kiểm tra scene.asset đã có → skip (idempotent)
  2. used_keywords.add(scene.search_keyword) để tránh trùng
  3. Nếu search_keyword đã dùng → append "different angle" / "alternative"
  4. Thử Pexels API: GET /videos/search?query={kw}&per_page=15
     - Lọc ratio >= 16:9 cho landscape, >= 9:16 cho shorts
     - Sort by duration (lấy clip dài nhất nếu cần cover)
     - Dedup toàn cục bằng set() asset.id
  5. Nếu Pexels rỗng (video):
     ├─► asset_type_needed == 'video':
     │     - Thử search_keywords_alt[0..2] trên Pexels
     │     - Nếu vẫn rỗng → PEXELS VIDEO FALLBACK sang PIXABAY VIDEO
     │     - Nếu vẫn rỗng → downcast sang ảnh (asset_type_needed = 'image')
     │       và tiếp tục chain ảnh bên dưới
     │
     └─► asset_type_needed == 'image':
           - PEXELS IMAGE
           - PIXABAY IMAGE
           - 🆕 UNSPLASH (chèn ảnh tĩnh chất lượng cao giữa transitions)
           - Cuối cùng: asset_status='no_result', để user manual upload

  6. Ghi SceneAsset vào scene.asset (provider ghi đúng: pexels|pixabay|unsplash)
  7. Update job progress
8. Cuối cùng: status=completed, COMMIT credit
```

**🆕 Unsplash (từ plan3.md) — Vai trò cụ thể:**

| Ưu điểm | Use case |
|---------|----------|
| Ảnh tĩnh chất lượng rất cao (chuyên nghiệp, 4K+) | Chèn vào **giữa các transitions** (scene chuyển tiếp) |
| API miễn phí 50 req/hr (Demo) / 5000 req/hr (Production) | Khi Pexels/Pixabay hết kết quả cho từ khóa hiếm |
| License rất thoáng (Unsplash License) | Dùng thoải mái không cần attribution |

```python
# apps/worker/services/asset_providers.py — thêm Unsplash
UNSPLASH_ENDPOINTS = {
    'search': 'https://api.unsplash.com/search/photos',
}

def search_unsplash(keyword: str, per_page: int = 15, orientation: str = 'landscape') -> list[dict]:
    """Unsplash chỉ trả ảnh, không có video. Dùng làm fallback cho image asset."""
    headers = {'Authorization': f'Client-ID {os.environ["UNSPLASH_ACCESS_KEY"]}'}
    params = {
        'query': keyword,
        'per_page': per_page,
        'orientation': orientation,  # 'landscape' | 'portrait' | 'squarish'
        'content_filter': 'high',   # lọc nội dung không phù hợp
    }
    resp = requests.get(UNSPLASH_ENDPOINTS['search'], headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get('results', [])
    return [{
        'id':           r['id'],
        'type':         'image',
        'download_url': r['urls']['full'],      # URL ảnh gốc (gọi lại để trigger download)
        'thumbnail_url':r['urls']['small'],
        'width':        r['width'],
        'height':       r['height'],
        'provider':     'unsplash',
        'license':      'unsplash',
        'author':       r['user']['name'],
    } for r in results]
```

**Rate limit chú ý:**
- Unsplash Demo: 50 req/hr (đủ cho MVP).
- Unsplash Production: 5000 req/hr (cần apply approval).
- Phase 1: dùng Demo key, monitor usage.



**Bước C — Realtime notify:** Supabase Realtime push update cho client.

---

## 10a. State Machine 14 Bước & Chained LLM Calls *(MỚI)*

> Tích hợp từ `DNA_plan.md` — quy trình 14 bước "Master Prompt" chống AI Slop.
> Bản chất v1 của prompt này là **Chatbot Prompt** (chờ user nhập liệu từng bước) — **không thể nhét nguyên vào Backend**. Phải **decouple** thành các AI call độc lập.

### 10a.1. Bảng 14 trạng thái & cách map vào Backend

| State | Tên | Loại | Trong SaaS Backend |
|-------|-----|------|---------------------|
| **1** | Thu thập Link kênh | Input | Form `/assistants/new` → user nhập URL |
| **2** | Upload 3-5 kịch bản | Input | **Auto**: Worker tự cào transcripts (xem §10b) |
| **3** | Xác định chủ đề | Input | Form `/projects/new` → user nhập topic |
| **4** | Channel X-Ray Analysis | **AI Call 1a** | `tasks/style_dna.py::xray_analysis()` |
| **5** | Style DNA Extraction | **AI Call 1b** | `tasks/style_dna.py::extract_dna()` |
| **5b** | 🆕 RAG indexing | Auto | `services/rag_indexer.py::index_transcripts_to_rag()` |
| **6** | Script Generation | **AI Call 2** | `tasks/script_gen.py::generate()` |
| **6b** | 🆕 Channel-Specific Title Generation | **AI Call 2b** | `tasks/titles.py::generate_channel_titles()` (xem §10d.5) |
| **7** | Thu thập thumbnails gốc | Input | Worker crawl thumbnail URLs của top videos |
| **8** | Visual / Thumbnail Analysis | **AI Call 3** | `tasks/visual.py::analyze_thumbnails()` (GPT-4o vision) |
| **8b** | 🆕 AI Thumbnail Generation | **AI Call 3b** | `tasks/thumbnail_gen.py::generate_thumbnail()` (§10d.6, dùng gpt-image-1) |
| **9** | Image Prompts (per 3-5s) | **AI Call 4** | `tasks/scene_breakdown.py::generate_scene_assets()` |
| **10** | Video Prompts | (gộp vào 9) | Mỗi scene có `visual_context` cho B-roll |
| **11** | Negative Prompts | Tùy chọn | Có thể bỏ qua Phase 1, dùng Pexels thay AI gen |
| **12** | Quality Check & Refinement | **AI Call 5** | `tasks/script_gen.py::refine()` |
| **13** | Tạo Variations | **AI Call 6** | `tasks/script_gen.py::variations()` (Phase 3) |
| **13b** | 🆕 Cross-Niche Transfer (Bend Niche) | **AI Call 6b** | `tasks/bend_niche.py::bend_niche()` (§10d.8) |
| **14** | Đóng gói & Export | Output | API trả về JSON toàn bộ + UI export buttons |

### 10a.2. Chained LLM Calls — Implementation

```python
# apps/worker/tasks/style_dna.py
from celery import shared_task
from .prompts.xray import XRAY_PROMPT
from .prompts.style_dna import STYLE_DNA_PROMPT_V2  # mới, có 3 layers
from .services.transcript import fetch_top_transcripts
from .services.llm import call_llm, log_api_call

@shared_task(bind=True, max_retries=2)
def extract_dna_pipeline(self, assistant_id: str, user_id: str, seed_channel_url: str):
    """State 1-2-4-5: Input → Auto-fetch transcripts → X-Ray → Style DNA."""
    sb = get_supabase_service()
    job_id = self.request.id

    try:
        sb.table('jobs').update({'status': 'running', 'progress': 10}).eq('id', job_id).execute()

        # ===== STATE 1-2: Auto-fetch transcripts =====
        transcripts = fetch_top_transcripts(
            channel_url=seed_channel_url,
            top_k=5,                # lấy 5 video viral nhất
            method='outlier',       # xem §10b
        )
        if len(transcripts) < 2:
            raise ValueError("Kênh không có đủ video có transcript để phân tích.")

        sb.table('jobs').update({'progress': 30}).eq('id', job_id).execute()

        # ===== STATE 4: X-Ray Analysis =====
        xray_result = call_llm(
            prompt=XRAY_PROMPT.format(transcripts=join(transcripts)),
            model='gpt-4o',
            json_mode=True,
            response_schema=ChannelXRay,
        )
        log_api_call(sb, user_id=user_id, job_id=job_id,
                     provider='openai', model='gpt-4o',
                     purpose='xray_analysis', **xray_result.usage)

        sb.table('jobs').update({'progress': 60}).eq('id', job_id).execute()

        # ===== STATE 5: Style DNA =====
        dna_result = call_llm(
            prompt=STYLE_DNA_PROMPT_V2.format(
                xray=xray_result.content,
                transcripts=join(transcripts),
            ),
            model='gpt-4o',
            json_mode=True,
            response_schema=StyleDNAProfileV2,  # mở rộng, xem §10a.4
        )
        log_api_call(sb, user_id=user_id, job_id=job_id,
                     provider='openai', model='gpt-4o',
                     purpose='style_dna_extract', **dna_result.usage)

        # ===== Lưu DB =====
        sb.table('channel_assistants').update({
            'style_dna_profile': dna_result.content,
            'xray_profile': xray_result.content,
        }).eq('id', assistant_id).execute()

        sb.table('jobs').update({'status': 'completed', 'progress': 100}).eq('id', job_id).execute()

    except Exception as e:
        sb.table('jobs').update({'status': 'failed', 'error': str(e)}).eq('id', job_id).execute()
        raise
```

### 10a.3. State 4 — Channel X-Ray (mới bổ sung)

Output là JSON phân tích tổng quan kênh (ngách, khán giả, kỹ thuật giữ chân):

```python
# apps/worker/prompts/xray.py
XRAY_PROMPT = """You are a YouTube channel strategist.

I will give you 5 transcripts from a channel. Perform a deep X-RAY analysis.
Return JSON:

{{
  "niche": "<short niche label>",
  "audience_persona": {{
    "age_range": "e.g. 18-34",
    "primary_interest": "<...>",
    "pain_points": ["<...>", "<...>"],
    "aspirations": ["<...>", "<...>"]
  }},
  "emotional_pacing_curve": [
    {{"phase": "hook",   "emotion": "curiosity",   "intensity": 9}},
    {{"phase": "setup",  "emotion": "fascination", "intensity": 7}},
    {{"phase": "buildup","emotion": "tension",     "intensity": 8}},
    {{"phase": "payoff", "emotion": "satisfaction","intensity": 10}},
    {{"phase": "cta",    "emotion": "urgency",     "intensity": 6}}
  ],
  "retention_techniques": [
    "open loops (promise answer at minute 5)",
    "pattern interrupts every 45 seconds",
    "controversy hooks",
    "..." 
  ],
  "thumbnail_patterns": ["bright colors", "face close-up", "..."],
  "title_formulas": ["How X without Y", "The TRUTH about Z", "..."]
}}

Transcripts:
{transcripts}

Return ONLY the JSON."""
```

### 10a.4. Style DNA v2 — 3 lớp (mở rộng từ v1)

Thay vì JSON phẳng như §12.1, dùng schema phân lớp:

```python
class StyleDNAV2(BaseModel):
    """3-layer DNA: writing style + content structure + emotional cues.

    🆕 Mở rộng từ §10e (Deep Channel Analysis) — bổ sung các trường OverseerOS-style:
    persona, pacing_profile, emotional_signature, hook_categories, mimic_rules, brand_assets.
    """

    # Layer 1: Writing Style (giống v1 + bổ sung 🆕 persona, wpm, mimic_rules)
    writing_style: WritingStyleLayer

    # Layer 2: Content Structure (mới + 🆕 structural_formula 9 bước)
    structure: StructureLayer

    # Layer 3: Emotional & Retention (mới từ DNA_plan.md + 🆕 emotional_signature %)
    retention: RetentionLayer

    # 🆕 MỚI từ §10e — các trường Deep Analysis
    persona: str = Field(
        default='',
        min_length=10, max_length=200,
        description='e.g., "Grounded empathetic financial mentor"'
    )
    pacing_profile: PacingProfile | None = None           # §10e.5
    emotional_signature: EmotionalSignature | None = None # §10e.5
    hook_categories: HookCategoriesAnalysis | None = None # §10e.6
    structural_formula: StructuralFormula | None = None   # §10e.7
    viral_topics_formula: list[dict] | None = None        # §10e.8
    mimic_rules: MimicToneGuideline | None = None         # §10e.9
    brand_assets: BrandAssets | None = None               # §10e.10


class WritingStyleLayer(BaseModel):
    hook_patterns: list[str]
    vocabulary_tier: Literal['casual', 'conversational', 'formal', 'academic']
    avg_sentence_length: int
    pacing: Literal['slow', 'medium', 'fast']
    signature_phrases: list[str]
    rhetorical_devices: list[str]
    tone_keywords: list[str]
    example_hooks: list[str]


class StructureLayer(BaseModel):
    typical_intro_seconds: int = Field(ge=5, le=120)
    typical_outro_seconds: int = Field(ge=5, le=120)
    sections_per_video: int
    section_templates: list[str]   # e.g. ["problem → promise → demo → proof → CTA"]
    transition_phrases: list[str]  # "Now here's the crazy part..."
    curiosity_gaps_per_minute: float = Field(ge=0, le=5)


class RetentionLayer(BaseModel):
    emotion_curve: list[EmotionPoint]   # mirror từ X-Ray nhưng định lượng hơn
    open_loop_count_avg: int
    pattern_interrupt_cadence_sec: int
    cta_type: Literal['subscribe', 'comment', 'next_video', 'lead_magnet']
    cta_position: Literal['mid_video', 'outro', 'both']
```

> **Các schema phụ `PacingProfile`, `EmotionalSignature`, `HookCategoriesAnalysis`, `StructuralFormula`, `MimicToneGuideline`, `BrandAssets`** được định nghĩa chi tiết trong §10e.5 → §10e.10.

### 10a.5. State 6 → 7 → 8 — Script + Thumbnail

```python
# apps/worker/tasks/script_gen.py
@shared_task(bind=True)
def generate_script(self, project_id: str, user_id: str, topic: str, assistant_id: str):
    """State 6 + bonus State 12 quality check."""
    sb = get_supabase_service()
    dna = load_dna(assistant_id)
    job_id = self.request.id

    # STATE 6: Viết kịch bản (Critical Visual Rule: KHÔNG nghĩ về hình ảnh)
    raw = call_llm(
        prompt=SCRIPT_GEN_PROMPT_V2.format(  # xem §11.2 có comment chống AI Slop
            style_dna=json.dumps(dna, ensure_ascii=False),
            topic=topic,
        ),
        model='gpt-4o',
        max_tokens=8000,
    )

    # STATE 12: Quality check (tự chấm)
    refined = call_llm(
        prompt=REFINE_SCRIPT_PROMPT.format(
            script=raw,
            style_dna=json.dumps(dna, ensure_ascii=False),
        ),
        model='gpt-4o',
    )

    sb.table('content_projects').update({
        'raw_script': refined,
        'status': 'script_ready',
    }).eq('id', project_id).execute()
```

### 10a.6. State 7-8 — Thumbnail Analysis *(bonus, Phase 2)*

Worker tự crawl thumbnails → dùng **GPT-4o vision** phân tích pattern:

```python
# apps/worker/tasks/visual.py
@shared_task(bind=True)
def analyze_thumbnails(self, assistant_id: str, user_id: str):
    """State 7 + 8: Crawl thumbnails of top 20 videos → GPT-4o vision analysis."""
    sb = get_supabase_service()
    asst = load_assistant(assistant_id)
    
    # 1. Lấy top 20 videos viral
    videos = get_top_videos(asst['seed_channel_id'], limit=20, method='outlier')
    thumbnails = [v['thumbnail_url'] for v in videos]
    
    # 2. GPT-4o vision
    analysis = call_llm_vision(
        images=thumbnails,
        prompt=THUMBNAIL_ANALYSIS_PROMPT,
        json_mode=True,
    )
    
    sb.table('channel_assistants').update({
        'thumbnail_profile': analysis,
    }).eq('id', assistant_id).execute()
```

Prompt: xem `apps/worker/prompts/thumbnail.py`.

### 10a.7. State 14 — Đóng gói & Export

API trả về file JSON tổng hợp, UI có nút export:

```
GET /api/projects/{id}/export?format=json|markdown|zip
```

JSON bao gồm:
- `topic`, `assistant_id`
- `raw_script` (text)
- `scenes_data` (array scenes đã có B-roll URL)
- `style_dna_profile`, `xray_profile`, `thumbnail_profile`
- `metadata`: { generated_at, model_versions, total_cost_usd, credits_charged }

---

## 10b. Outlier Strength & Video Viral Selection *(MỚI)*

> Trích từ `DNA_plan.md` §Giai đoạn 1: cần chọn **3-5 video viral nhất** để bóc tách. Nhưng "viral" ≠ "nhiều view nhất". Cần thuật toán **Outlier Strength**.

### 10b.1. Định nghĩa Outlier Strength

Một video được coi là **outlier** khi nó vượt trội so với kênh trung bình:

```
outlier_score = (video.views / channel_avg_views) × freshness_decay
```

Trong đó:
- `channel_avg_views` = trung bình view của 50 video gần nhất của kênh.
- `freshness_decay` = `1.0 / (1 + months_since_publish × 0.1)` — video cũ hơn bị giảm điểm.

### 10b.2. Implementation

```python
# apps/worker/services/transcript.py
from datetime import datetime
import statistics

def compute_outlier_score(video_views: int, channel_avg_views: int, published_at: datetime) -> float:
    if channel_avg_views <= 0:
        return 0
    months_old = (datetime.utcnow() - published_at).days / 30
    decay = 1.0 / (1 + months_old * 0.1)
    return (video_views / channel_avg_views) * decay

def fetch_top_transcripts(channel_url: str, top_k: int = 5, method: str = 'outlier') -> list[dict]:
    """Lấy transcripts của top K video theo outlier score (mặc định)."""
    
    # Bước 1: channels.list → channel_id, uploads_playlist_id (1 quota)
    channel = youtube.channels().list(forHandle=extract_handle(channel_url), part='id,contentDetails').execute()
    channel_id = channel['items'][0]['id']
    uploads_pl = channel['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # Bước 2: playlistItems.list → 50 video mới nhất (1 quota)
    items = youtube.playlistItems().list(playlistId=uploads_pl, maxResults=50, part='contentDetails').execute()
    video_ids = [it['contentDetails']['videoId'] for it in items['items']]
    
    # Bước 3: videos.list → stats (1 quota)
    stats = youtube.videos().list(id=','.join(video_ids), part='statistics,snippet').execute()
    
    # Bước 4: Tính channel_avg_views
    all_views = [int(v['statistics'].get('viewCount', 0)) for v in stats['items']]
    channel_avg = statistics.mean(all_views) if all_views else 0
    
    # Bước 5: Tính outlier_score, sort desc
    scored = []
    for v in stats['items']:
        views = int(v['statistics'].get('viewCount', 0))
        published = datetime.fromisoformat(v['snippet']['publishedAt'].replace('Z', '+00:00')).replace(tzinfo=None)
        score = compute_outlier_score(views, channel_avg, published)
        scored.append({
            'video_id': v['id'],
            'title': v['snippet']['title'],
            'views': views,
            'published_at': published.isoformat(),
            'outlier_score': score,
            'thumbnail_url': v['snippet']['thumbnails']['high']['url'],
        })
    
    # Method 'outlier' vs 'absolute'
    if method == 'absolute':
        scored.sort(key=lambda x: x['views'], reverse=True)
    else:
        scored.sort(key=lambda x: x['outlier_score'], reverse=True)
    
    top = scored[:top_k]
    
    # Bước 6: Lấy transcript cho từng video (free hoặc Whisper fallback)
    for item in top:
        item['transcript'] = fetch_transcript(item['video_id'])
    
    return top
```

### 10b.3. Lưu outlier_score vào DB

```sql
-- supabase/migrations/0003_outlier.sql
alter table public.channel_assistants
  add column outlier_videos jsonb;  -- [{video_id, title, views, outlier_score, transcript}, ...]
```

### 10b.4. Caching

- Cache Redis 24h key `yt:channel:{channel_id}:top_outlier:{top_k}` → tránh gọi lại YouTube khi user test nhiều lần.
- Invalidate khi user chọn "Refresh".

---

## 10c. Critical Visual Rule & Anti-AI-Slop *(MỚI)*

> Trích từ `DNA_plan.md` §"Critical Visual Rule": **không được nghĩ về hình ảnh trước khi script hoàn thiện**.

### 10c.1. Nguyên tắc cứng

> **CRITICAL VISUAL RULE**: Khi viết kịch bản (Phase 2.2), AI **TUYỆT ĐỐI KHÔNG** được:
> - Đề cập đến hình ảnh cụ thể ("hãy hiển thị hình một người đang chạy")
> - Chèn stage direction (`[VISUAL: ...]`)
> - Phân chia cảnh (`Scene 1: ... Scene 2: ...`)
> - Nghĩ về B-roll, thumbnail, hay bất cứ thứ gì thuộc về hình ảnh.
>
> **Lý do:** LLM có xu hướng "đầu tư" token vào mô tả hình ảnh thay vì cải thiện văn phong → dẫn đến "AI Slop".

### 10c.2. Áp dụng vào SCRIPT_GEN_PROMPT

```python
SCRIPT_GEN_PROMPT_V2 = """You are a YouTube scriptwriter who mimics a specific style.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL VISUAL RULE — DO NOT VIOLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
While writing this script you MUST NOT:
  - Mention any specific image, footage, or B-roll.
  - Insert stage directions like [VISUAL: ...] or [SHOW: ...].
  - Divide the script into scenes.
  - Think about thumbnails, color grading, music, or visuals.
Your ONLY job right now is to write EXCELLENT TEXT.
A separate AI pass will handle visuals AFTER the script is done.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STYLE DNA (you MUST follow strictly):
{style_dna}

TOPIC: {topic}

RULES:
- Hook (first 30 seconds): use ONE pattern from hook_patterns verbatim.
- Target length: ~{target_minutes} minutes spoken at 150 wpm.
- Maintain vocabulary_tier and pacing.
- Include signature_phrases at least 3 times.
- Include retention techniques from DNA.retention (open loops, pattern interrupts, curiosity gaps).
- End with a CTA matching dna.retention.cta_type.

OUTPUT: the full script as plain flowing text. NO markdown. NO scene numbers. NO visual cues."""
```

### 10c.3. Anti-AI-Slop Rules (thêm vào DNA prompt)

```python
ANTI_AI_SLOP_RULES = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-AI-SLOP RULES — these words/phrases are FORBIDDEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Never use these AI-sounding crutch phrases:
  - "Let's dive in" / "Let's explore"
  - "In this video, we'll..."
  - "Without further ado"
  - "Game-changer" / "game-changing"
  - "Unlock the secrets"
  - "Buckle up"
  - "Picture this"
  - "Imagine a world where..."
  - "It's not just X, it's Y"
  - Em-dashes used as dramatic pauses (—)
  - Bullet-list-style transitions ("First... Second... Finally...")
  - Paragraphs starting with "So," "Now," "Alright," more than 3 times.

Use instead:
  - Concrete sensory detail (specific numbers, named objects, real dates)
  - Asymmetric sentence structure (mix 5-word and 30-word sentences)
  - First-person experience ("I tried...", "Last Tuesday I...")
  - Mild profanity at strategic moments if DNA allows
  - Self-deprecating humor if DNA allows
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

### 10c.4. REFINE_SCRIPT_PROMPT (State 12)

Sau khi viết xong, chạy AI chấm và sửa:

```python
REFINE_SCRIPT_PROMPT = """You are a script editor. Review the script below against the STYLE DNA.

STEP 1: Score the script on 5 dimensions (1-10 each):
  - hook_strength
  - pacing_match
  - vocabulary_match
  - retention_techniques_used
  - ai_slop_score (10 = ZERO slop, 1 = full of clichés)

STEP 2: List 3-5 specific improvements as a list.

STEP 3: Output the REWRITTEN script with those improvements applied.

Return JSON:
{{
  "scores": {{"hook_strength": int, ...}},
  "improvements": ["...", "..."],
  "rewritten_script": "..."
}}

STYLE DNA: {style_dna}
SCRIPT: {script}"""
```

### 10c.5. Detect AI Slop tự động (heuristic)

```python
# apps/worker/utils/anti_slop.py
AI_SLOP_PHRASES = [
    "let's dive in", "without further ado", "buckle up",
    "unlock the secrets", "picture this", "game-changer",
    "imagine a world", "in today's video", "it's not just",
    "first and foremost",
]

def detect_slop_density(text: str) -> float:
    """Trả về tỷ lệ slop / 1000 từ."""
    words = text.lower().split()
    if not words: return 0
    slop_hits = sum(1 for p in AI_SLOP_PHRASES if p in text.lower())
    return (slop_hits / len(words)) * 1000

# Block nếu slop_density > 2
```

### 10c.6. State 14 — Quality Gate trước khi trả về user

```python
def quality_gate(script: str, dna: dict) -> tuple[bool, list[str]]:
    errors = []
    if detect_slop_density(script) > 2:
        errors.append("script has too much AI slop")
    if not any(p in script for p in dna['writing_style']['signature_phrases']):
        errors.append("script missing signature phrases")
    if count_open_loops(script) < 3:
        errors.append("script has fewer than 3 open loops")
    return (len(errors) == 0, errors)
```

### 10c.7. 🆕 Few-Shot Prompting + RAG cho Anti-AI-Slop *(từ plan3.md)*

> Trích từ `plan3.md` §2: tham chiếu repo `mikiarlo3/ai-copywriter`.
> "AI Slop" là nguyên nhân chính khiến kênh dùng AI thất bại vì retention thấp.
> Hệ thống sử dụng **Few-Shot Prompting + RAG** để ép LLM tuân theo DNA đã bóc tách.

### 10c.7.1. Kiến trúc RAG

```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE INDEXING                          │
│  (chạy 1 lần khi tạo Assistant)                             │
│                                                              │
│  5 transcripts gốc                                           │
│       ↓                                                       │
│  Chunk: mỗi chunk = 1 đoạn 3-7 câu (semantic split)         │
│       ↓                                                       │
│  Embedding: OpenAI text-embedding-3-small (1536 dims)        │
│       ↓                                                       │
│  Store: Supabase pgvector (table: dna_chunks)                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   ONLINE GENERATION                          │
│  (chạy mỗi lần viết kịch bản)                               │
│                                                              │
│  User nhập topic + assistant_id                              │
│       ↓                                                       │
│  Embedding topic                                              │
│       ↓                                                       │
│  Top-K=8 chunks liên quan (cosine similarity > 0.7)          │
│       ↓                                                       │
│  Inject vào prompt dưới dạng FEW-SHOT EXAMPLES               │
│       ↓                                                       │
│  LLM generate script                                         │
└─────────────────────────────────────────────────────────────┘
```

### 10c.7.2. Schema bảng RAG

```sql
-- supabase/migrations/0004_rag.sql
create extension if not exists vector;

create table public.dna_chunks (
  id uuid primary key default uuid_generate_v4(),
  assistant_id uuid not null references public.channel_assistants(id) on delete cascade,
  chunk_text text not null,
  chunk_meta jsonb not null default '{}',  -- {type: 'hook'|'body'|'transition', source_video_id}
  embedding vector(1536) not null,
  created_at timestamptz not null default now()
);

create index dna_chunks_assistant_idx on public.dna_chunks(assistant_id);
create index dna_chunks_embedding_idx on public.dna_chunks
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);

alter table public.dna_chunks enable row level security;
create policy "dna_chunks_owner_all" on public.dna_chunks
  for all using (
    assistant_id in (
      select id from public.channel_assistants where user_id = public.current_user_id()
    )
  );
```

### 10c.7.3. Code indexing

```python
# apps/worker/services/rag_indexer.py
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def index_transcripts_to_rag(assistant_id: str, transcripts: list[dict]) -> int:
    """Build pgvector index từ transcripts. Chạy 1 lần khi tạo Assistant."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=80,
        separators=['\n\n', '\n', '. ', '? ', '! '],
    )

    chunks = []
    for t in transcripts:
        for chunk in splitter.split_text(t['text']):
            chunks.append({
                'text': chunk,
                'meta': {'type': 'body', 'source_video_id': t['video_id']},
            })

    # Embed in batch (OpenAI supports up to 2048 inputs / request)
    response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=[c['text'] for c in chunks],
    )

    sb = get_supabase_service()
    rows = [{
        'assistant_id': assistant_id,
        'chunk_text': c['text'],
        'chunk_meta': c['meta'],
        'embedding': emb.embedding,
    } for c, emb in zip(chunks, response.data)]

    # Batch insert 100 rows / lần
    for i in range(0, len(rows), 100):
        sb.table('dna_chunks').insert(rows[i:i+100]).execute()

    return len(rows)
```

### 10c.7.4. Code retrieval

```python
# apps/worker/services/rag_retriever.py
from openai import OpenAI
import os

openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def retrieve_relevant_chunks(assistant_id: str, query: str, top_k: int = 8,
                              min_similarity: float = 0.7) -> list[dict]:
    """Trả về top-K chunks giống query nhất (cosine similarity)."""
    emb_response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query,
    )
    query_emb = emb_response.data[0].embedding

    sb = get_supabase_service()
    # pgvector cosine distance: <=> operator, similarity = 1 - distance
    result = sb.rpc('match_dna_chunks', {
        'p_assistant_id': assistant_id,
        'p_query_embedding': query_emb,
        'p_match_count': top_k,
        'p_min_similarity': min_similarity,
    }).execute()

    return result.data or []


# SQL function: supabase/migrations/0005_rag_function.sql
# create or replace function match_dna_chunks(
#   p_assistant_id uuid, p_query_embedding vector(1536),
#   p_match_count int, p_min_similarity float
# ) returns table (id uuid, chunk_text text, chunk_meta jsonb, similarity float)
# language sql stable as $$
#   select id, chunk_text, chunk_meta,
#          1 - (embedding <=> p_query_embedding) as similarity
#   from dna_chunks
#   where assistant_id = p_assistant_id
#     and 1 - (embedding <=> p_query_embedding) > p_min_similarity
#   order by embedding <=> p_query_embedding
#   limit p_match_count;
# $$;
```

### 10c.7.5. SCRIPT_GEN_PROMPT với RAG

```python
# apps/worker/prompts/script_gen_v2.py
SCRIPT_GEN_PROMPT_WITH_RAG = """You are a YouTube scriptwriter who mimics a specific style.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL VISUAL RULE — DO NOT VIOLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
While writing this script you MUST NOT mention any specific image, footage, B-roll,
insert stage directions, divide into scenes, or think about visuals.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANTI-AI-SLOP RULES — these words/phrases are FORBIDDEN:
  "let's dive in", "without further ado", "buckle up", "unlock the secrets",
  "picture this", "game-changer", "imagine a world", "in today's video",
  "it's not just", "first and foremost".
Use concrete sensory detail, asymmetric sentences, first-person experience instead.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE DNA (you MUST follow strictly):
{style_dna}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES — these are real snippets from the channel.
Match their tone, structure, and vocabulary exactly:
{few_shot_chunks}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOPIC: {topic}
TARGET LENGTH: ~{target_minutes} minutes @ 150 wpm

OUTPUT: full script as plain flowing text. NO markdown. NO scene numbers. NO visuals."""
```

### 10c.7.6. Integration vào pipeline

```python
# apps/worker/tasks/script_gen.py (bổ sung)
from ..services.rag_retriever import retrieve_relevant_chunks

@shared_task(bind=True)
def generate_script(self, project_id, user_id, topic, assistant_id):
    sb = get_supabase_service()
    dna = load_dna(assistant_id)
    job_id = self.request.id

    # RAG retrieval
    chunks = retrieve_relevant_chunks(assistant_id, query=topic, top_k=8)
    few_shot = '\n\n---\n\n'.join(f"[Example {i+1}]\n{c['chunk_text']}"
                                   for i, c in enumerate(chunks))

    # LLM with RAG context
    raw = call_llm(
        prompt=SCRIPT_GEN_PROMPT_WITH_RAG.format(
            style_dna=json.dumps(dna, ensure_ascii=False),
            few_shot_chunks=few_shot,
            topic=topic,
            target_minutes=8,
        ),
        model='gpt-4o',
        max_tokens=8000,
    )
    # ... refine + save như cũ
```

### 10c.7.7. Lợi ích Few-Shot + RAG

| Vấn đề | Không có RAG | Có RAG |
|---------|--------------|---------|
| LLM "tự chế" từ vựng | Bị generic, sounding AI | Lấy đúng từ vựng channel |
| Hook lines | Một vài pattern lặp lại | Mỗi lần lấy hook khác nhau từ corpus |
| Pacing | Estimate sai | Thấy đoạn thật → bắt chước chính xác |
| Signature phrases | Bị LLM "quên" dần sau 4000 tokens | Inject trực tiếp vào prompt |

### 10c.7.8. Chi phí bổ sung

| Action | Cost ước tính |
|--------|---------------|
| Indexing (1 lần) | 5 transcripts × ~600 chunks = 600 embeddings × $0.02/1M = **~$0.0001** |
| Query (mỗi script) | 1 embedding + 8 chunks (free từ DB) = **~$0.0000002** |
| Supabase pgvector storage | Free tier đủ cho 10K chunks/user |

→ Gần như **miễn phí**, trade-off rất nhỏ so với lợi ích chống AI Slop.

---

## 10d. Channel Blueprint — 6 Power Features *(MỚI)*

> Phân tích từ screenshot "Building Your Channel Blueprint" — sau khi user nhập 1 kênh, hệ thống cung cấp **6 "superpowers"** để khai thác DNA kênh đó cho việc sản xuất nội dung.
>
> 3 trong 6 đã có rải rác trong PRD: Script Gen (§10a), Viral Scan (§10b), Find Channels (§9).
> **3 điểm mới cần xây**: AI-generate thumbnail (không chỉ analyze), Bend Niche (chuyển ngách giữ format), Titles theo winning formula.

### 10d.1. Mapping 6 features vào Backend hiện có

| # | Feature | Screen label | State tương ứng | Đã có? | AI Call mới? |
|---|---------|--------------|------------------|--------|---------------|
| 1 | **Write scripts in their tone** | "Write scripts" | State 6 (Script Gen) + RAG (§10c.7) | ✅ Đã có | Có (gọi lại với DNA hiện tại) |
| 2 | **Scan their viral videos** | "Identify viral videos" | Outlier selection (§10b) + X-Ray (§10a.3) | ✅ Đã có | Không (tổng hợp từ DB) |
| 3 | **Create titles in their style** | "Generate titles" | **🆕 Title Generator** | ❌ Mới | Có |
| 4 | **Generate thumbnails in their style** | "Thumbnail generator" | **🆕 AI Thumbnail Gen** (gpt-image-1 / DALL-E 3) | ⚠️ Partial (chỉ analysis §10a.6) | Có |
| 5 | **Find viral channels in their niche** | "Discover niche" | Module 1 (§9) với keyword = channel niche | ✅ Đã có | Không |
| 6 | **Bend this channel's niche** | "Apply to new niche" | **🆕 Cross-Niche Transfer** | ❌ Mới | Có |

### 10d.2. UI/UX Blueprint Progress Screen

> Spec cho màn hình progress (xem screenshot): hiển thị ngay khi user vừa submit "Analyze this channel".

**Layout (Next.js client component):**

```
┌────────────────────────────────────────────────────────────────┐
│  Building Your Channel Blueprint                               │
│  We're extracting [ChanName]'s secret sauce: hooks, pacing...  │
│                                                                 │
│  ●────●────●────●────○────○────○────○                            │
│  1    2    3    4    5    6    7    8                            │
│  Crawl  X-Ray DNA  RAG  Virus  Title Thumb Niche                │
│                                                                 │
│  ┌─────────────────────┐   ┌──────────────────────────────┐    │
│  │ Currently working:  │   │ ✅ Hoàn thành (4):            │    │
│  │ 🔄 Building RAG     │   │ • Crawl transcripts          │    │
│  │    index...         │   │ • X-Ray analysis             │    │
│  │                     │   │ • Extract Style DNA          │    │
│  │ 3 of 8 steps done   │   │ • Index chunks into pgvector │    │
│  └─────────────────────┘   │                              │    │
│                              │ ⏳ Waiting (4):              │    │
│  ┌─────────────────────┐   │ • Identify viral videos      │    │
│  │ Blueprint Powers:   │   │ • Generate titles            │    │
│  │ [Write scripts]     │   │ • AI thumbnail gen           │    │
│  │ [Scan viral]        │   │ • Bend niche                 │    │
│  │ [Create titles]     │   └──────────────────────────────┘    │
│  │ [Gen thumbnails]    │                                         │
│  │ [Find channels]     │   Estimated time remaining: ~2 min     │
│  │ [Bend niche]        │                                         │
│  └─────────────────────┘                                         │
└────────────────────────────────────────────────────────────────┘
```

**8-Step Timeline:**

| Step | Tên hiển thị | Backend task | Avg time |
|------|---------------|--------------|----------|
| 1 | Crawl transcripts | `fetch_top_transcripts()` | 5-10s |
| 2 | X-Ray analysis | `xray_analysis()` | 15-30s |
| 3 | Extract Style DNA v2 | `extract_dna()` | 20-40s |
| 4 | Index chunks into pgvector | `index_transcripts_to_rag()` | 10-15s |
| 5 | Identify viral videos | tổng hợp outlier_videos đã có | 2s |
| 6 | Generate titles | **`generate_titles()` (MỚI)** | 10s |
| 7 | AI thumbnail gen | **`generate_thumbnail()` (MỚI)** | 20-30s |
| 8 | Bend niche | **`bend_niche()` (MỚI)** | 15-25s |

**Implementation:**

```typescript
// apps/web/components/BlueprintProgress.tsx
'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

const STEPS = [
  { id: 1, label: 'Crawl',      task: 'fetch_transcripts' },
  { id: 2, label: 'X-Ray',      task: 'xray_analysis' },
  { id: 3, label: 'DNA',        task: 'dna_extraction' },
  { id: 4, label: 'RAG',        task: 'rag_indexing' },
  { id: 5, label: 'Viral scan', task: 'identify_viral' },
  { id: 6, label: 'Titles',     task: 'generate_titles' },       // 🆕
  { id: 7, label: 'Thumbnails', task: 'generate_thumbnail' },    // 🆕
  { id: 8, label: 'Bend niche', task: 'bend_niche' },            // 🆕
];

export function BlueprintProgress({ assistantId }: { assistantId: string }) {
  const [completed, setCompleted] = useState<Set<number>>(new Set());
  const [current, setCurrent] = useState<number>(1);

  useEffect(() => {
    const channel = supabase
      .channel(`blueprint:${assistantId}`)
      .on('broadcast', { event: 'step_complete' }, (payload) => {
        setCompleted(prev => new Set([...prev, payload.step_id]));
        setCurrent(payload.step_id + 1);
      })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [assistantId]);

  return (
    <div>
      <Stepper steps={STEPS} completed={completed} current={current} />
      <PowersGrid disabled={current < 8} />  {/* các nút power bị disable cho tới khi xong step 4 */}
    </div>
  );
}
```

### 10d.3. Feature #1 — Write Scripts in Their Tone

**UI button:** `Write scripts` → mở editor modal
**Backend:** §10a.5 + §10c.7.6 (đã có sẵn — không cần build mới)
**API endpoint:** `POST /api/projects` (đã có trong §5)

**New UX touch:** trong editor có "Side panel DNA" hiển thị:
- Hook patterns (kèm ví dụ thật từ RAG retrieval)
- Signature phrases đã được LLM nhúng vào script
- Slop density score realtime (`detect_slop_density`)

### 10d.4. Feature #2 — Scan Their Viral Videos

**UI button:** `Identify viral videos` → mở dashboard
**Backend:** §10b Outlier Strength + X-Ray (§10a.3) — đã có sẵn
**Điểm mới:** Hiển thị *tại sao* video viral, không chỉ là viral score:

```python
# apps/worker/services/viral_analysis.py
def explain_viral(video: OutlierVideo, xray: ChannelXRay) -> dict:
    """Kết hợp outlier_score + xray để giải thích tại sao video viral."""
    return {
        'video_id': video.video_id,
        'title': video.title,
        'views': video.views,
        'outlier_score': video.outlier_score,
        'reasons': [
            f"Uses title formula: '{xray['title_formulas'][0]}'",
            f"Matches hook pattern: '{xray['retention_techniques'][0]}'",
            f"Emotional peak in {xray['emotional_pacing_curve'][2]['phase']} phase",
            f"Published on best-performing day for this channel",
        ],
        'copyable_elements': {
            'hook_template': extract_hook(video.transcript),
            'thumbnail_concept': extract_visual_concept(video.thumbnail_url),
            'structure_breakdown': ...,
        },
    }
```

### 10d.5. Feature #3 🆕 — Create Titles in Their Style

**UI button:** `Generate titles` → form nhập topic, nhận 10 titles
**Backend:** AI Call mới, dùng **winning formula** từ DNA analysis (khác với titles trong Module 1 — đó là general; cái này là **channel-specific**)

```python
# apps/worker/tasks/titles.py
@shared_task(bind=True)
def generate_channel_titles(self, assistant_id: str, user_id: str, topic: str,
                              count: int = 10):
    """State 6b: Tạo tiêu đề theo winning formula của riêng kênh đó."""
    sb = get_supabase_service()
    dna = load_dna(assistant_id)
    job_id = self.request.id

    # RAG: lấy 15 titles viral nhất của channel
    viral_titles = sb.table('channel_assistants') \
        .select('outlier_videos').eq('id', assistant_id).single().execute()
    examples = [v['title'] for v in viral_titles.data['outlier_videos'][:15]]

    # Prompt: ép LLM tuân theo title_formulas đã extract từ X-Ray
    prompt = CHANNEL_TITLE_PROMPT.format(
        style_dna=json.dumps(dna, ensure_ascii=False),
        title_formulas=dna.get('xray_profile', {}).get('title_formulas', []),
        example_titles='\n'.join(f"- {t}" for t in examples),
        topic=topic,
        count=count,
    )

    result = call_llm(prompt, model='gpt-4o', json_mode=True,
                       response_schema=TitleSuggestions)

    sb.table('generated_titles').insert({
        'assistant_id': assistant_id,
        'user_id': user_id,
        'topic': topic,
        'titles': result.titles,
        'created_at': 'now()',
    }).execute()
```

```python
# apps/worker/prompts/channel_title.py
CHANNEL_TITLE_PROMPT = """You are a viral YouTube title writer.

You will write titles in the EXACT style of the channel "{channel_name}".
This channel's WINNING TITLE FORMULAS (extracted from X-Ray analysis):
{title_formulas}

These are real viral titles from the channel (analyze the PATTERNS, do not copy):
{example_titles}

STYLE DNA — additional context:
{style_dna}

TOPIC for new titles: {topic}

Generate {count} titles that:
1. Follow the winning formulas above strictly
2. Match the channel's vocabulary tier and tone
3. Are in {language}
4. Max 70 characters
5. Use curiosity gaps, numbers, emotion where proven to work
6. Are COMPLETELY ORIGINAL — never copy any example title verbatim

Return JSON: {{"titles": ["title1", "title2", ...], "reasoning": "..."}}"""
```

**JSON Schema:**

```python
class ChannelTitleSuggestions(BaseModel):
    titles: list[str] = Field(min_length=5, max_length=20)
    reasoning: str = Field(min_length=50)

# Bảng DB mới:
# supabase/migrations/0006_titles.sql
# create table public.generated_titles (
#   id uuid primary key default uuid_generate_v4(),
#   user_id uuid not null,
#   assistant_id uuid references channel_assistants(id),
#   topic text not null,
#   titles jsonb not null,         -- ["title1", "title2", ...]
#   reasoning text,
#   created_at timestamptz default now()
# );
```

### 10d.6. Feature #4 🆕 — Generate Thumbnails in Their Style

**UI button:** `Generate thumbnails` → form nhập title, AI gen thumbnail
**Backend:** AI image generation (DALL-E 3 / gpt-image-1), dùng **thumbnail_profile** (§10a.6) làm style guide

> ⚠️ QUAN TRỌNG: §10a.6 chỉ **analyze** thumbnails. Đây là bước **generate** mới.

```python
# apps/worker/tasks/thumbnail_gen.py
@shared_task(bind=True)
def generate_thumbnail(self, assistant_id: str, user_id: str, video_title: str,
                        count: int = 4):
    """AI-generate thumbnail theo style của channel."""
    sb = get_supabase_service()
    thumb_profile = load_thumbnail_profile(assistant_id)
    job_id = self.request.id

    # Dựng prompt từ thumbnail_profile
    image_prompt = build_thumbnail_prompt(thumb_profile, video_title)

    # Generate 4 variants (OpenAI gpt-image-1)
    results = []
    for i in range(count):
        img = openai_client.images.generate(
            model='gpt-image-1',  # hoặc 'dall-e-3'
            prompt=image_prompt,
            size='1280x720',     # YouTube thumbnail ratio
            quality='high',
            n=1,
        )
        results.append({
            'variant_id': i + 1,
            'image_url': img.data[0].url,
            'revised_prompt': img.data[0].revised_prompt,
        })

    # Lưu vào Supabase Storage + record vào DB
    stored = []
    for r in results:
        path = f"thumbnails/{user_id}/{assistant_id}/{job_id}_{r['variant_id']}.png"
        download_and_upload(r['image_url'], path)
        stored.append({'storage_path': path, 'revised_prompt': r['revised_prompt']})

    sb.table('generated_thumbnails').insert({
        'assistant_id': assistant_id,
        'user_id': user_id,
        'video_title': video_title,
        'variants': stored,
        'created_at': 'now()',
    }).execute()
```

```python
# apps/worker/prompts/thumbnail_gen.py
def build_thumbnail_prompt(profile: ThumbnailProfile, video_title: str) -> str:
    """Convert ThumbnailProfile JSON → image generation prompt."""
    palette = ', '.join(profile.color_palette[:3])
    layouts = ', '.join(profile.dominant_layouts[:2])
    text_overlay = profile.text_overlay_style
    common_words = ', '.join(text_overlay.common_words[:3])

    return f"""YouTube thumbnail in this EXACT style:

VISUAL LAYOUT: {layouts}
COLOR PALETTE (use these): {palette}
TEXT OVERLAY: bold sans-serif font saying 1-3 words (typical: "{common_words}")
TEXT STYLE: {text_overlay.font_style}, maximum {text_overlay.typical_word_count} words
BACKGROUND: {', '.join(profile.background_patterns[:2])}
EMOTIONAL TRIGGERS: {', '.join(profile.emotional_triggers[:3])}

VIDEO TITLE: "{video_title}"
CONCEPT: a striking visual that creates curiosity about {video_title}

CRITICAL RULES:
- 1280x720 ratio
- No watermarks, no real brand logos
- High contrast, instantly readable at small size
- Text must be HUGE and bold
- Do NOT look like generic stock photo
- Style must be an EXTREME version of the channel's style
"""
```

**🆕 Bảng DB:**

```sql
-- supabase/migrations/0007_thumbnails.sql
create table public.generated_thumbnails (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id),
  assistant_id uuid not null references public.channel_assistants(id),
  video_title text not null,
  variants jsonb not null,             -- [{variant_id, storage_path, revised_prompt}, ...]
  credits_used int not null default 4,
  created_at timestamptz default now()
);
alter table public.generated_thumbnails enable row level security;
create policy "thumbnails_owner_all" on public.generated_thumbnails
  for all using (user_id = public.current_user_id());
```

### 10d.7. Feature #5 — Find Viral Channels in Their Niche

**UI button:** `Discover niche` → nhảy sang Module 1 dashboard, prefill keyword = `niche` từ X-Ray
**Backend:** §9 Module 1 — tái sử dụng hoàn toàn, chỉ prefill `keyword = channel.niche`

```typescript
// apps/web/app/(app)/blueprint/[id]/discover-button.tsx
'use client';
import { useRouter } from 'next/navigation';

export function DiscoverButton({ niche }: { niche: string }) {
  const router = useRouter();
  return (
    <Button onClick={() => router.push(`/research?keyword=${encodeURIComponent(niche)}`)}>
      🔍 Find viral channels in "{niche}"
    </Button>
  );
}
```

### 10d.8. Feature #6 🆕 — Bend This Channel's Niche

**Concept:** Giữ nguyên format/hooks/pacing/retention của kênh A, nhưng áp dụng sang **niche B hoàn toàn khác** (e.g. channel làm `Personal Finance` → user muốn dùng công thức đó cho `Pet Care`).

**UI button:** `Bend niche` → form chọn target_niche + topic
**Backend:** AI Call mới, dựa trên **DNA abstraction** (tách phong cách ra khỏi chủ đề)

```python
# apps/worker/tasks/bend_niche.py
@shared_task(bind=True)
def bend_niche(self, source_assistant_id: str, user_id: str, target_niche: str,
                topic: str | None = None):
    """Cross-niche transfer: format từ kênh A, nội dung sang ngách B."""
    sb = get_supabase_service()
    dna = load_dna(source_assistant_id)
    job_id = self.request.id

    # Tách DNA thành 2 phần: STYLE (giữ) + CONTENT (thay)
    style_only = {
        'writing_style': dna['writing_style'],   # giữ 100%
        'structure':     dna['structure'],        # giữ 100%
        'retention':     dna['retention'],        # giữ 100%
    }
    niche_specific = {
        'xray_profile':  dna.get('xray_profile'), # BỎ — đặc thù niche cũ
        'thumbnail_profile': ...,                 # BỎ
    }

    # RAG retrieval từ target_niche (nếu đã có assistant khác trong target_niche)
    # Hoặc dùng general knowledge nếu chưa có
    target_examples = []
    target_assistant = find_assistant_by_niche(user_id, target_niche)
    if target_assistant:
        target_examples = retrieve_relevant_chunks(target_assistant.id, topic, top_k=8)

    prompt = BEND_NICHE_PROMPT.format(
        style_dna=json.dumps(style_only, ensure_ascii=False),
        source_niche=load_assistant(source_assistant_id)['niche'],
        target_niche=target_niche,
        target_examples=format_examples(target_examples),
        topic=topic or f"general {target_niche}",
    )

    bent_script = call_llm(prompt, model='gpt-4o', max_tokens=8000)

    # Lưu như 1 project mới với flag is_bent_from
    new_project_id = sb.table('content_projects').insert({
        'user_id': user_id,
        'source_assistant_id': source_assistant_id,
        'target_niche': target_niche,
        'topic': topic,
        'raw_script': bent_script,
        'status': 'script_ready',
    }).execute().data[0]['id']

    return new_project_id
```

```python
# apps/worker/prompts/bend_niche.py
BEND_NICHE_PROMPT = """You are a cross-niche content strategist.

The user wants to take the FORMAT and STYLE of channel A and apply it to channel B's niche.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — ABSTRACT the DNA into transferable patterns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You will receive a StyleDNA JSON. Your first task is to mentally separate:
- STYLE elements (transferable across niches): hook patterns, pacing, signature phrases,
  rhetorical devices, structure, retention techniques
- NICHE elements (NOT transferable): specific topic vocabulary, niche metaphors,
  audience persona assumptions

Keep ONLY the STYLE elements. Discard niche-specific assumptions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — GENERATE script for TARGET niche
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source channel: {source_niche}
Target niche:   {target_niche}
Topic:          {topic}

STYLE TO TRANSFER (DO follow):
{style_dna}

RAG EXAMPLES from target niche (if available, follow vocabulary):
{target_examples}

CRITICAL: 
- The writing must feel like the SOURCE channel's format
- BUT the content must be entirely about the TARGET niche
- Like a "format transplant": same skeleton, different body
- No mixing of metaphors from source niche into target content

CRITICAL VISUAL RULE: Do NOT mention any visuals in the output.

OUTPUT: a complete script in plain text."""
```

**🆕 Bảng DB bổ sung cột:**

```sql
-- supabase/migrations/0008_bent_projects.sql
alter table public.content_projects
  add column source_assistant_id uuid references public.channel_assistants(id),
  add column target_niche text;
```

### 10d.9. API Endpoints mới

```python
# apps/api/app/routers/blueprint.py
@router.post("/assistants/{assistant_id}/titles", response_model=ChannelTitleSuggestions)
async def generate_titles(assistant_id: UUID, body: TitleGenRequest, user = Depends(auth)):
    """Feature #3 — Create titles in their style."""
    job_id = uuid4()
    generate_channel_titles.delay(str(assistant_id), user.id, body.topic, body.count, str(job_id))
    return {"job_id": str(job_id), "status": "queued"}

@router.post("/assistants/{assistant_id}/thumbnails", response_model=ThumbnailGenResponse)
async def generate_thumbnails(assistant_id: UUID, body: ThumbnailGenRequest,
                               user = Depends(auth)):
    """Feature #4 — AI gen thumbnails."""
    job_id = uuid4()
    generate_thumbnail.delay(str(assistant_id), user.id, body.video_title, body.count, str(job_id))
    return {"job_id": str(job_id), "status": "queued", "estimated_seconds": 30}

@router.post("/assistants/{assistant_id}/bend-niche", response_model=BendNicheResponse)
async def bend_niche(assistant_id: UUID, body: BendNicheRequest,
                      user = Depends(auth)):
    """Feature #6 — Cross-niche transfer."""
    new_project_id = bend_niche.delay(str(assistant_id), user.id,
                                       body.target_niche, body.topic).get()
    return {"new_project_id": str(new_project_id), "status": "script_ready"}
```

### 10d.10. Credit Cost mới

| Feature | Credits/sử dụng | Free tier? |
|---------|------------------|------------|
| Write Scripts (đã có) | 5 credits | 5 lần/tháng |
| Scan Viral (đã có) | 0 (chỉ tổng hợp) | Unlimited |
| **🆕 Generate Titles (channel-style)** | 1 credit / 10 titles | 5 lần/tháng |
| **🆕 Generate Thumbnails** | 4 credits / 4 variants | 3 lần/tháng |
| Find Viral Channels (đã có) | 3 credits / search | 5 lần/tháng |
| **🆕 Bend Niche** | 8 credits | 2 lần/tháng |

### 10d.11. Upsell flow

Khi user click vào power mà credit = 0 → modal "Upgrade to Pro" hiện ra. Flow này đã có trong §8.2 (credit tier), chỉ cần hook vào UI.

---

## 10e. Deep Channel Analysis — OverseerOS-style Report *(MỚI)*

> Phân tích từ `ana_plan1.md` + `ana_plan2.md` — workflow của tool OverseerOS áp dụng reverse-engineering sâu vào kênh "Chú Béo Tài Chính" và tạo ra một bản Blueprint toàn diện gồm **13 đầu ra phân tích** (đã thấy 11 screenshot).
>
> Mục tiêu: app của chúng ta phải generate báo cáo y hệt (hoặc tốt hơn), bao gồm cả phần "Hidden Insights" và "Untapped Opportunities".

### 10e.1. 13 Outputs Mapping

| # | Output | Section trong PRD hiện tại | Trạng thái |
|---|--------|----------------------------|------------|
| 1 | **Metadata & Performance** (schedule, duration, title length) | §10e.3 (MỚI) | 🆕 Mới |
| 2 | **Tags co-occurrence + viral ratio** | §10e.3 (MỚI) | 🆕 Mới |
| 3 | **Hidden Insights** (consistency score, optimal duration range) | §10e.4 (MỚI) | 🆕 Mới |
| 4 | **Persona Description** | §10a.4 style DNA — bổ sung `persona` field | 🆕 Mới |
| 5 | **Word Density (wpm)** | §10e.5 (MỚI) | 🆕 Mới |
| 6 | **Emotional Signature** (35/25/20/15/5%) | §10e.5 (MỚI) | 🆕 Mới |
| 7 | **Signature Phrases** | §10a.4 — đã có | ✅ Có sẵn |
| 8 | **Hook Categories** (3-4 loại hook có tên) | §10e.6 (MỚI) | 🆕 Mới |
| 9 | **Structural Formula 9 bước** | §10e.7 (MỚI) | 🆕 Mới |
| 10 | **Viral Topics Formula** (Vì Sao [X]?) | §10e.8 (MỚI) | 🆕 Mới |
| 11 | **How to Mimic Tone** (11 nguyên tắc) | §10e.9 (MỚI) | 🆕 Mới |
| 12 | **Channel Strategy + About + Description Template + Top Tags + Keywords + Slogans** | §10e.10 (MỚI) | 🆕 Mới |
| 13 | **Untapped Opportunities** (gap analysis) | §10e.11 (MỚI) | 🆕 Mới |

**Kết luận:** 12/13 outputs là hoàn toàn mới, cần xây dựng. PRD hiện tại chỉ có **Signature Phrases** từ §10a.4.

### 10e.2. Kiến trúc pipeline Deep Analysis

> Tích hợp vào Phase 1 của Channel Blueprint (8-step timeline trong §10d.2) — thay thế Step 2 "X-Ray" và Step 3 "Extract DNA" thành một **Deep Analysis** 2-3 AI call lớn hơn.

```
┌─────────────────────────────────────────────────────────────┐
│  OFFLINE (chạy sau khi user submit channel URL)              │
│                                                              │
│  Step 0:  YouTube API crawl                                  │
│            → 50 video gần nhất + transcripts + thumbnails    │
│                                                              │
│  Step 1:  🆕 METADATA ANALYSIS (deterministic)              │
│            → wpm, duration, title length, schedule, tags    │
│            → 100% code Python, KHÔNG cần AI                  │
│                                                              │
│  Step 2:  🆕 X-RAY DEEP (AI call 1a) — chunked             │
│            → 5 transcript × 4 phân tích = 20 sub-call       │
│            → persona, emotional_signature, hook_categories   │
│                                                              │
│  Step 3:  🆕 FORMULA EXTRACTION (AI call 1b)                 │
│            → structural_formula, viral_topics_formula,       │
│              how_to_mimic_tone (11 rules)                    │
│                                                              │
│  Step 4:  🆕 BRAND ASSETS (AI call 1c)                       │
│            → about_template, description_template,          │
│              keywords[], slogans[]                           │
│                                                              │
│  Step 5:  🆕 HIDDEN INSIGHTS + UNTAPPED OPPORTUNITIES        │
│            → deterministic (insights) + AI call 1d (gaps)    │
│                                                              │
│  Output:  BLUEPRINT_REPORT JSON (~50KB)                      │
└─────────────────────────────────────────────────────────────┘
```

### 10e.3. Output #1+2 — Metadata & Tags Analysis (Deterministic)

> **Không cần AI call** — chỉ cần Python thuần tính toán từ raw YouTube data. Rẻ và chính xác tuyệt đối.

```python
# apps/worker/services/metadata_analysis.py
from collections import Counter
from datetime import datetime, timedelta
import statistics
from itertools import combinations


def analyze_metadata(videos: list[Video]) -> dict:
    """Trả về MetadataReport — deterministic, không qua AI."""
    return {
        'schedule': analyze_schedule(videos),
        'duration': analyze_duration(videos),
        'title_length': analyze_title_length(videos),
        'tags': analyze_tags(videos),
        'word_density': compute_wpm(videos),  # cần có transcript ở đây
    }


def analyze_schedule(videos: list[Video]) -> dict:
    """Output #1a — Upload cadence analysis."""
    upload_dates = sorted([v.published_at for v in videos if v.published_at])
    gaps_days = [
        (upload_dates[i+1] - upload_dates[i]).days
        for i in range(len(upload_dates) - 1)
    ]
    if not gaps_days:
        return {'avg_gap_days': 0, 'consistency_score': 0}

    avg_gap = statistics.mean(gaps_days)
    std_gap = statistics.stdev(gaps_days) if len(gaps_days) > 1 else 0
    # consistency_score: 100 = hoàn hảo đều, 0 = rất thất thường
    consistency_score = max(0, 100 - int((std_gap / avg_gap) * 100))

    return {
        'avg_videos_per_month': round(30 / avg_gap, 1),
        'avg_gap_days': round(avg_gap, 1),
        'std_gap_days': round(std_gap, 1),
        'consistency_score': consistency_score,   # 0-100
        'verdict': (
            'highly_consistent' if consistency_score >= 80
            else 'consistent' if consistency_score >= 60
            else 'inconsistent' if consistency_score >= 40
            else 'very_inconsistent'
        ),
    }


def analyze_duration(videos: list[Video]) -> dict:
    """Output #1b — Optimal duration cluster."""
    long_form = [v.duration_sec for v in videos if v.duration_sec >= 600]  # ≥10min
    shorts = [v.duration_sec for v in videos if v.duration_sec < 60]

    return {
        'long_form': {
            'count': len(long_form),
            'optimal_range': compute_cluster_range(long_form),  # e.g. "18:04-20:28"
            'median_seconds': int(statistics.median(long_form)) if long_form else 0,
            'best_performing': find_best_duration(long_form, videos),
        },
        'shorts': {
            'count': len(shorts),
            'avg_seconds': int(statistics.mean(shorts)) if shorts else 0,
        },
    }


def analyze_title_length(videos: list[Video]) -> dict:
    """Output #1c — Optimal title length."""
    char_counts = [len(v.title) for v in videos]
    word_counts = [len(v.title.split()) for v in videos]

    return {
        'avg_chars': round(statistics.mean(char_counts), 1),
        'avg_words': round(statistics.mean(word_counts), 1),
        'optimal_chars': int(statistics.median(char_counts)),
        'optimal_words': int(statistics.median(word_counts)),
        'best_performing_chars': find_best_title_length(videos),
    }


def analyze_tags(videos: list[Video]) -> dict:
    """Output #2 — Tag co-occurrence + viral ratio."""
    # 1. Đếm tần suất
    tag_counter = Counter()
    for v in videos:
        tag_counter.update(v.tags or [])

    # 2. Top tags
    top_tags = [{'tag': t, 'count': c, 'pct': round(c / len(videos) * 100, 1)}
                for t, c in tag_counter.most_common(20)]

    # 3. Tag co-occurrence pairs
    pairs = Counter()
    for v in videos:
        sorted_tags = sorted(set(v.tags or []))
        for pair in combinations(sorted_tags, 2):
            pairs[pair] += 1
    top_pairs = [{'pair': list(p), 'count': c}
                 for p, c in pairs.most_common(10)]

    # 4. Viral tag ratio: % viral videos chứa tag X
    viral_threshold = max(v.view_count for v in videos) * 0.3
    viral_videos = [v for v in videos if v.view_count >= viral_threshold]
    viral_tag_ratio = {
        tag: round(
            sum(1 for v in viral_videos if tag in (v.tags or [])) / max(len(viral_videos), 1) * 100,
            1,
        )
        for tag, _ in tag_counter.most_common(20)
    }

    # 5. Diversity + saturation
    unique_tags = len(tag_counter)

    return {
        'top_tags': top_tags,
        'top_co_occurring_pairs': top_pairs,
        'viral_tag_ratio': viral_tag_ratio,
        'total_unique_tags': unique_tags,
        'avg_tags_per_video': round(statistics.mean([len(v.tags or []) for v in videos]), 1),
        'optimal_tag_count': int(statistics.mode([len(v.tags or []) for v in videos])),
    }
```

**JSON Output:**

```json
{
  "schedule": {
    "avg_videos_per_month": 12,
    "avg_gap_days": 2.5,
    "consistency_score": 65,
    "verdict": "consistent"
  },
  "duration": {
    "long_form": {
      "count": 42,
      "optimal_range": "18:04-20:28",
      "median_seconds": 1174,
      "best_performing": 1152
    }
  },
  "title_length": {
    "avg_chars": 56.3,
    "optimal_chars": 58,
    "optimal_words": 13
  },
  "tags": {
    "top_tags": [{"tag": "tài chính cá nhân", "count": 31, "pct": 62.0}],
    "viral_tag_ratio": {"tài chính cá nhân": 78.0},
    "total_unique_tags": 223,
    "optimal_tag_count": 6
  }
}
```

### 10e.4. Output #3 — Hidden Insights (Deterministic + Heuristic)

> Hidden Insights = **những pattern ẩn** mà con người khó phát hiện nhưng code có thể tính ra.

```python
# apps/worker/services/hidden_insights.py
def discover_hidden_insights(metadata: dict, viral_videos: list[Video]) -> list[dict]:
    """Trả về list các insights có giải thích + recommended action."""
    insights = []

    # Insight 1 — Top performing tag
    top_tag = metadata['tags']['top_tags'][0]
    insights.append({
        'rank': 1,
        'category': 'tag',
        'title': f"Tag \"{top_tag['tag']}\" là vũ khí bí mật",
        'data_point': f"xuất hiện trong {top_tag['pct']}% video viral",
        'recommendation': f"Áp dụng tag này vào MỌI video mới trong niche này",
        'severity': 'high',
    })

    # Insight 2 — Tag diversity vs optimal count
    if metadata['tags']['optimal_tag_count'] != round(metadata['tags']['avg_tags_per_video']):
        insights.append({
            'rank': 2,
            'category': 'tag',
            'title': f"Số lượng tag tối ưu khác xa trung bình",
            'data_point': f"Optimal={metadata['tags']['optimal_tag_count']} vs Avg={metadata['tags']['avg_tags_per_video']}",
            'recommendation': f"Dùng chính xác {metadata['tags']['optimal_tag_count']} tags thay vì {round(metadata['tags']['avg_tags_per_video'])}",
            'severity': 'medium',
        })

    # Insight 3 — Posting consistency
    score = metadata['schedule']['consistency_score']
    verdict = metadata['schedule']['verdict']
    insights.append({
        'rank': 3,
        'category': 'schedule',
        'title': f"Tần suất đăng: {verdict.replace('_', ' ')}",
        'data_point': f"Consistency score: {score}/100",
        'recommendation': (
            "Đăng đều mỗi 2-3 ngày để thuật toán đề xuất bạn"
            if score < 80 else "Duy trì nhịp độ hiện tại"
        ),
        'severity': 'high' if score < 50 else 'low',
    })

    # Insight 4 — Optimal duration range
    insights.append({
        'rank': 4,
        'category': 'duration',
        'title': f"Duration cluster: {metadata['duration']['long_form']['optimal_range']}",
        'data_point': f"{compute_cluster_percentage(viral_videos, metadata['duration']['long_form']['optimal_range'])}% video viral nằm trong range này",
        'recommendation': f"Target thời lượng {metadata['duration']['long_form']['optimal_range']} cho mọi video long-form",
        'severity': 'high',
    })

    # Insight 5 — Tag saturation analysis
    saturation = analyze_tag_saturation(viral_videos)
    insights.append({
        'rank': 5,
        'category': 'tag_saturation',
        'title': f"{saturation['untapped_count']} tags có tiềm năng chưa khai thác",
        'data_point': f"{saturation['balanced_count']} balanced | {saturation['overused_count']} overused | {saturation['untapped_count']} untapped",
        'recommendation': "Sử dụng các untapped tags cho video mới — ít cạnh tranh hơn",
        'severity': 'high',
    })

    # Insight 6 — Common viral title word
    common_word = find_common_viral_word(viral_videos)
    if common_word:
        insights.append({
            'rank': 6,
            'category': 'title',
            'title': f"Từ khóa \"{common_word['word']}\" xuất hiện trong {common_word['pct']}% tiêu đề viral",
            'data_point': f"Word: \"{common_word['word']}\"",
            'recommendation': f"Ưu tiên đặt từ này ở đầu title formula",
            'severity': 'medium',
        })

    # Insight 7 — Success formula
    formula_pct = compute_success_formula_match(viral_videos)
    insights.append({
        'rank': 7,
        'category': 'meta_formula',
        'title': f"Công thức thành công: Duration {metadata['duration']['long_form']['optimal_range']} + ≥10 tags",
        'data_point': f"{formula_pct}% video viral match công thức này",
        'recommendation': "Áp dụng song song 2 yếu tố khi upload",
        'severity': 'high',
    })

    return insights
```

**JSON Output:**

```json
{
  "hidden_insights": [
    {
      "rank": 1,
      "category": "tag",
      "title": "Tag \"tài chính cá nhân\" là vũ khí bí mật",
      "data_point": "xuất hiện trong 62% video viral",
      "recommendation": "Áp dụng tag này vào MỌI video mới trong niche này",
      "severity": "high"
    }
  ]
}
```

### 10e.5. Output #5+6 — Word Density (wpm) + Emotional Signature

> Cần **AI call** nhưng có thể làm 1 lần duy nhất, output structured.

```python
# apps/worker/prompts/wpm_emotional.py
WPM_EMOTIONAL_PROMPT = """You are analyzing 5 transcripts from a Vietnamese YouTube channel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK 1 — WORD DENSITY (WPM)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each transcript:
1. Count the total words (Vietnamese words separated by spaces).
2. Note the video duration (in seconds).
3. Calculate WPM = words / (duration / 60).
4. Return avg, min, max wpm across 5 transcripts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK 2 — SENTENCE TREND (PACING PROFILE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Describe in 3-5 sentences how the SENTENCE LENGTH varies throughout the video:
- Where does the author use short punchy sentences?
- Where does the author use long flowing sentences?
- Is there a rhythm/pattern?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK 3 — EMOTIONAL SIGNATURE DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Allocate percentage (must sum to 100%) of overall emotional tone:
- empathy       — % of content that validates/mirrors audience feelings
- curiosity     — % that creates information gaps
- authority     — % that establishes expertise
- urgency       — % that drives action
- mystery       — % that hints at hidden knowledge
- reassurance   — % that calms anxiety
- inspiration   — % that motivates

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK 4 — DOMINANT EMOTION LABEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pick ONE emotion label (e.g., "Empowered clarity", "Triumphant discovery")
that best describes the channel's overall emotional tone.

Return JSON only.
"""
```

**JSON Schema (mở rộng StyleDNA):**

```python
class PacingProfile(BaseModel):
    avg_wpm: int
    min_wpm: int
    max_wpm: int
    sentence_trend: str = Field(min_length=100, max_length=500)


class EmotionalSignature(BaseModel):
    empathy: int = Field(ge=0, le=100)
    curiosity: int = Field(ge=0, le=100)
    authority: int = Field(ge=0, le=100)
    urgency: int = Field(ge=0, le=100)
    mystery: int = Field(ge=0, le=100)
    reassurance: int = Field(ge=0, le=100)
    inspiration: int = Field(ge=0, le=100)
    dominant_label: str

    @model_validator(mode='after')
    def check_sum(self):
        total = sum([self.empathy, self.curiosity, self.authority,
                     self.urgency, self.mystery, self.reassurance, self.inspiration])
        if total != 100:
            raise ValueError(f'emotional percentages must sum to 100, got {total}')
        return self
```

### 10e.6. Output #8 — Hook Categories (phân loại Hook có tên)

> PRD hiện tại có `count_open_loops()` đếm số open loops nhưng chưa phân loại hook. OverseerOS-style cần **4-6 categories có tên**.

```python
# apps/worker/prompts/hook_categories.py
HOOK_CATEGORY_PROMPT = """You are analyzing opening lines of 5 viral YouTube scripts.

For EACH opening line, do the following:
1. Extract the opening line verbatim (first 2-3 sentences)
2. Classify it into ONE of these hook categories:
   - "experiential_mirror" — describes viewer's situation in 2nd person
   - "alarming_statistic" — leads with a striking number, then humanizes it
   - "contrarian_challenge" — challenges a common belief directly
   - "rhetorical_question" — opens with a question that creates curiosity
   - "sensory_immersion" — paints a vivid sensory scene immediately
   - "first_person_anecdote" — opens with personal story ("Năm tôi 24 tuổi...")
   - "data_reframe" — presents data in a surprising context
   - "direct_address_empathy" — directly acknowledges viewer's pain

3. Provide a one-sentence description of the pattern

Return JSON: {
  "hooks": [
    {
      "transcript_id": 1,
      "verbatim": "Anh em có biết cái cảm giác này không?...",
      "category": "experiential_mirror",
      "description": "Mô tả trải nghiệm cảm xúc bằng ngôi thứ hai"
    }
  ],
  "category_distribution": {
    "experiential_mirror": 2,
    "alarming_statistic": 1,
    "contrarian_challenge": 1,
    ...
  },
  "dominant_hook_type": "experiential_mirror"
}
"""
```

**JSON Schema:**

```python
HookCategoryEnum = Literal[
    'experiential_mirror',
    'alarming_statistic',
    'contrarian_challenge',
    'rhetorical_question',
    'sensory_immersion',
    'first_person_anecdote',
    'data_reframe',
    'direct_address_empathy',
]

class ExtractedHook(BaseModel):
    transcript_id: int
    verbatim: str = Field(min_length=20, max_length=500)
    category: HookCategoryEnum
    description: str

class HookCategoriesAnalysis(BaseModel):
    hooks: list[ExtractedHook]
    category_distribution: dict[HookCategoryEnum, int]
    dominant_hook_type: HookCategoryEnum
    recommended_hook_template: str = Field(
        description='A reusable template based on dominant category'
    )
```

### 10e.7. Output #9 — Structural Formula (9 bước)

> OverseerOS-style dùng **9 bước tuyến tính cố định** — khác với high-level structure hiện tại của PRD.

```python
# apps/worker/prompts/structural_formula.py
STRUCTURAL_FORMULA_PROMPT = """You are reverse-engineering the script structure of a Vietnamese YouTube channel.

Based on 5 analyzed transcripts, identify the RECURRING 9-step structural formula.

The formula should be LINEAR — each step appears in the same order across scripts.

Each step must have:
- step_number (1-9)
- name (short label in Vietnamese)
- description (1-2 sentences in Vietnamese explaining the technique)
- typical_position (in seconds, e.g., "0-30s", "30-90s", "5:00-7:00", "ending")
- example_phrase (a real snippet from the transcripts that demonstrates this step)

Use this template for the 9 steps (you may rename and adjust):

1. Opening Question to Engage Curiosity
2. Problem Statement with Relatable Scenarios
3. Introduction of Unconventional Insight
4. Contextual Background with Data and Statistics
5. Illustrative Analogy for Conceptual Clarity
6. Psychological Insight into Common Behaviors
7. Practical Steps or Solutions
8. Long-term Vision and Encouragement
9. Call to Action for Engagement

Return JSON: {
  "structural_formula": [
    {
      "step_number": 1,
      "name": "Câu hỏi mở đầu kích thích tò mò",
      "description": "...",
      "typical_position": "0-30s",
      "example_phrase": "Bạn đã bao giờ đẩy một chiếc xe máy hết xăng lên dốc chưa?"
    },
    ...
  ]
}
"""
```

**JSON Schema:**

```python
class StructuralStep(BaseModel):
    step_number: int = Field(ge=1, le=15)
    name: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=30, max_length=300)
    typical_position: str = Field(description='e.g., "0-30s" or "5:00-7:00"')
    example_phrase: str = Field(min_length=10, max_length=500)

class StructuralFormula(BaseModel):
    steps: list[StructuralStep] = Field(min_length=3, max_length=15)
    # Ví dụ OverseerOS: 9 steps; cho phép range 3-15
```

### 10e.8. Output #10 — Viral Topics Formula

```python
# apps/worker/prompts/viral_topics.py
VIRAL_TOPICS_PROMPT = """You are analyzing 50 viral video titles from a Vietnamese YouTube channel.

Identify the 5-10 RECURRING title formulas (templates with placeholders).

Each formula has:
- template: the literal template with placeholders in [BRACKETS]
- example_titles: 2-3 real titles that match this formula
- frequency: how many of the 50 titles match this formula
- why_it_works: 1 sentence explaining the psychological hook

Examples of formula types:
- "Vì Sao [ISSUE]?"
- "[NUMBER] [ITEM] [DESCRIPTION]"
- "Tại Sao [SITUATION]?"
- "Cách [ACTION] Để [OUTCOME]"
- "[PERSONAL_PRONOUN] [ACTION] Sau [TIME]"

Return JSON: {
  "viral_topics_formula": [
    {
      "template": "Vì Sao [ISSUE]?",
      "example_titles": [
        "Vì Sao 9/10 Người Việt Vẫn Mắc Nợ Mỗi Cuối Tháng?",
        "Vì Sao Tiết Kiệm Hay Làm Giàu?"
      ],
      "frequency": 12,
      "why_it_works": "Tạo curiosity gap về một vấn đề quen thuộc"
    }
  ]
}
"""
```

### 10e.9. Output #11 — How to Mimic Tone (11 Nguyên tắc)

> Đây là phần **quan trọng nhất** — chính là "guidelines" mà OverseerOS dùng để bắt chước giọng. Tương tự Anti-AI-Slop nhưng tích cực hơn (làm theo) thay vì cấm.

```python
# apps/worker/prompts/mimic_tone.py
MIMIC_TONE_PROMPT = """You are reverse-engineering the writing guidelines of a Vietnamese YouTube channel.

Generate EXACTLY 11 numbered rules that another writer (or AI) can follow
to write scripts in this channel's voice.

Each rule must:
1. Have a SHORT CAPS LABEL (English) as the heading
2. Have a detailed Vietnamese description (2-3 sentences)
3. Include 1-2 example phrases from the actual transcripts

Rules MUST cover these 11 categories (in order):
1. OPEN WITH EMOTIONAL MIRROR
2. VALIDATE BEFORE YOU EDUCATE
3. INTRODUCE A SURPRISING REFRAME
4. USE CONCRETE ANALOGIES ROOTED IN [CULTURE]
5. ANCHOR WITH PROVERBS / CULTURAL SAYINGS
6. BUILD WITH DATA, THEN HUMANIZE IT
7. PREEMPT OBJECTIONS OUT LOUD
8. STRUCTURE: Problem → Validate → Reframe → Evidence → Solution → Conclusion
9. KEEP VOCABULARY SIMPLE, MAKE NUMBERS SPECIFIC
10. END WITH A SPECIFIC ENGAGEMENT QUESTION
11. TONE IS 'TRUSTED OLDER SIBLING'

NOTE: Substitute [CULTURE] with the actual culture (Vietnamese, US, etc.)
based on the channel's primary language.

Return JSON: {
  "mimic_rules": [
    {
      "rule_number": 1,
      "label": "OPEN WITH EMOTIONAL MIRROR",
      "description": "...",
      "examples": ["Anh em có biết cái cảm giác này không?"]
    }
  ]
}
"""
```

**JSON Schema:**

```python
class MimicRule(BaseModel):
    rule_number: int = Field(ge=1, le=20)
    label: str = Field(min_length=5, max_length=100,
                        description='SHORT CAPS LABEL')
    description: str = Field(min_length=50, max_length=500)
    examples: list[str] = Field(min_length=1, max_length=3)

class MimicToneGuideline(BaseModel):
    rules: list[MimicRule] = Field(min_length=5, max_length=20)
    culture: str  # 'Vietnamese', 'US', 'UK', etc.
    tone_archetype: str  # 'trusted_older_sibling', 'intellectual_peer', etc.
```

### 10e.10. Output #12 — Channel Strategy & Brand Assets

> All-in-one: about + description template + top tags + keywords + slogans.

```python
# apps/worker/prompts/brand_assets.py
BRAND_ASSETS_PROMPT = """Based on the analyzed channel, generate:

1. about_template: A 3-4 paragraph "About This Channel" section
   - Mentions the niche and target audience
   - Includes emotional hook
   - 100-200 words

2. description_template: A reusable video description template
   - First 2 sentences mention the topic of THIS video (with {TOPIC} placeholder)
   - Middle paragraph describes what viewer will learn
   - Last paragraph includes hashtags
   - 150-250 words

3. channel_keywords: 15-20 SEO keywords extracted from
   video titles + tags + about section
   (comma-separated, mix of Vietnamese and English if applicable)

4. brand_slogans: 3-5 short slogans (5-10 words each)
   - Memorable, on-brand
   - Match the emotional signature

Return JSON: {
  "about_template": "...",
  "description_template": "Video này về {TOPIC}. ...",
  "channel_keywords": ["tài chính cá nhân", ...],
  "brand_slogans": ["Tài chính đơn giản, cuộc sống phong phú", ...]
}
"""
```

**JSON Schema:**

```python
class BrandAssets(BaseModel):
    about_template: str = Field(min_length=300, max_length=1500)
    description_template: str = Field(min_length=500, max_length=2000)
    channel_keywords: list[str] = Field(min_length=10, max_length=30)
    brand_slogans: list[str] = Field(min_length=3, max_length=8)
```

### 10e.11. Output #13 — Untapped Opportunities (Gap Analysis)

> Phần **có giá trị nhất** — tìm chủ đề chưa được khai thác bằng cách so sánh viral formula với actual published topics.

```python
# apps/worker/tasks/untapped_opportunities.py
@shared_task(bind=True)
def find_untapped_opportunities(self, assistant_id: str):
    """AI scan gap giữa (viral formulas + audience interests) và (published topics)."""
    sb = get_supabase_service()

    # Lấy dữ liệu đã có
    assistant = sb.table('channel_assistants').select('*, outlier_videos, blueprint_report').eq('id', assistant_id).single().execute()
    blueprint = assistant.data.get('blueprint_report', {})
    published_titles = [v['title'] for v in assistant.data.get('outlier_videos', [])]
    viral_formulas = blueprint.get('viral_topics_formula', [])

    # Lấy toàn bộ video (không chỉ outlier)
    all_videos = sb.table('video_archives').select('title,topic,published_at').eq('channel_id', assistant.data['channel_id']).execute()

    prompt = UNTAPPED_OPPORTUNITIES_PROMPT.format(
        viral_formulas=json.dumps(viral_formulas, ensure_ascii=False),
        all_published_titles='\n'.join(f"- {v['title']}" for v in all_videos.data[:200]),
        niche=blueprint.get('niche', ''),
        hidden_insights=json.dumps(blueprint.get('hidden_insights', []), ensure_ascii=False),
    )

    result = call_llm(prompt, model='gpt-4o', json_mode=True,
                       response_schema=UntappedOpportunities)

    # Lưu vào DB
    sb.table('untapped_opportunities').insert({
        'assistant_id': assistant_id,
        'opportunities': result.opportunities,
        'created_at': 'now()',
    }).execute()

    return result.opportunities
```

```python
# apps/worker/prompts/untapped_opportunities.py
UNTAPPED_OPPORTUNITIES_PROMPT = """You are a content strategist finding UNEXPLORED opportunities
for a Vietnamese YouTube channel.

The channel has these VIRAL TITLE FORMULAS (proven to work):
{viral_formulas}

These are PUBLISHED titles (already covered):
{all_published_titles}

The channel's niche: {niche}

Hidden insights from analysis:
{hidden_insights}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Find 5-10 video ideas that:
1. Match one of the viral formulas above
2. Are NOT a duplicate of any published title
3. Have not been over-saturated in the niche
4. Have potential to go viral

For each idea, return:
- title: a fully-formed title using one of the viral formulas
- format: 'long_form' | 'short'
- estimated_duration_min: [min, max]
- rating: 1-5 stars (based on viral potential)
- rationale: 1-2 sentences explaining why this is high-potential
- viral_formula_used: which formula template

Return JSON: {
  "opportunities": [
    {
      "title": "Tại Sao 9/10 Người Việt Vẫn Mắc Nợ Mỗi Cuối Tháng?",
      "format": "long_form",
      "estimated_duration_min": [10, 15],
      "rating": 5,
      "rationale": "Topic pain còn chưa được khai thác góc nhìn từ tệp gen Z, dùng formula 'Tại Sao' đã proven",
      "viral_formula_used": "Tại Sao [SITUATION]?"
    }
  ]
}
"""
```

**JSON Schema:**

```python
class Opportunity(BaseModel):
    title: str = Field(min_length=10, max_length=120)
    format: Literal['long_form', 'short']
    estimated_duration_min: tuple[int, int] = Field(
        description='[min, max] in minutes'
    )
    rating: int = Field(ge=1, le=5)
    rationale: str = Field(min_length=30, max_length=300)
    viral_formula_used: str

class UntappedOpportunities(BaseModel):
    opportunities: list[Opportunity] = Field(min_length=3, max_length=20)
```

### 10e.12. Bảng DB bổ sung cho Deep Analysis

```sql
-- supabase/migrations/0009_deep_analysis.sql

-- Bảng chính lưu report tổng
create table public.deep_analysis_reports (
  id uuid primary key default uuid_generate_v4(),
  assistant_id uuid not null references public.channel_assistants(id) on delete cascade,
  metadata jsonb not null,                -- §10e.3
  hidden_insights jsonb not null,        -- §10e.4
  pacing_profile jsonb,                  -- §10e.5
  emotional_signature jsonb,             -- §10e.5
  hook_categories jsonb,                 -- §10e.6
  structural_formula jsonb,              -- §10e.7
  viral_topics_formula jsonb,            -- §10e.8
  mimic_tone_rules jsonb,                -- §10e.9
  brand_assets jsonb,                    -- §10e.10
  generated_at timestamptz not null default now(),
  expires_at timestamptz,                -- nếu cache TTL
  unique (assistant_id, generated_at)
);

-- Bảng riêng cho Untapped Opportunities (thường được query/update độc lập)
create table public.untapped_opportunities (
  id uuid primary key default uuid_generate_v4(),
  assistant_id uuid not null references public.channel_assistants(id) on delete cascade,
  opportunities jsonb not null,          -- [Opportunity, ...]
  created_at timestamptz not null default now()
);

create index untapped_opp_assistant_idx on public.untapped_opportunities(assistant_id, created_at desc);

alter table public.deep_analysis_reports enable row level security;
alter table public.untapped_opportunities enable row level security;

create policy "deep_reports_owner_read" on public.deep_analysis_reports
  for select using (
    assistant_id in (
      select id from public.channel_assistants where user_id = public.current_user_id()
    )
  );
create policy "untapped_opp_owner_read" on public.untapped_opportunities
  for select using (
    assistant_id in (
      select id from public.channel_assistants where user_id = public.current_user_id()
    )
  );
```

### 10e.13. Tích hợp vào Channel Blueprint Progress (§10d.2)

> Update 8-step timeline: Step 2 "X-Ray" → Step 2 "Deep Analysis" (lớn hơn).

**Timeline cập nhật:**

| Step | Tên hiển thị | Backend task | Avg time |
|------|---------------|--------------|----------|
| 1 | Crawl transcripts | `fetch_top_transcripts()` | 5-10s |
| **2** | **🆕 Deep Analysis** | `metadata_analysis() → xray_deep() → formula_extract() → brand_assets() → untapped()` | **60-90s** |
| 3 | RAG indexing | `index_transcripts_to_rag()` | 10-15s |
| 4 | Identify viral videos | tổng hợp | 2s |
| 5 | Generate titles | `generate_titles()` | 10s |
| 6 | AI thumbnail gen | `generate_thumbnail()` | 20-30s |
| 7 | Bend niche | `bend_niche()` | 15-25s |
| 8 | Packaging | export report | 3s |

### 10e.14. API Endpoints mới

```python
# apps/api/app/routers/deep_analysis.py
@router.get("/assistants/{assistant_id}/report", response_model=DeepAnalysisReport)
async def get_report(assistant_id: UUID, user = Depends(auth)):
    """Trả về toàn bộ report (cached trong DB)."""
    return load_report(assistant_id)

@router.get("/assistants/{assistant_id}/opportunities", response_model=UntappedOpportunitiesResponse)
async def get_opportunities(assistant_id: UUID, user = Depends(auth)):
    """Trả về Untapped Opportunities mới nhất."""
    return load_opportunities(assistant_id)

@router.post("/assistants/{assistant_id}/opportunities/refresh", status_code=202)
async def refresh_opportunities(assistant_id: UUID, user = Depends(auth)):
    """Re-run gap analysis (mỗi lần ~30s, tốn 1 credit)."""
    find_untapped_opportunities.delay(str(assistant_id))
    return {"status": "queued"}
```

### 10e.15. UI/UX — Report Page

**Layout** (xem OverseerOS screenshots):

```
┌────────────────────────────────────────────────────────────────┐
│  [Channel Name] Blueprint                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│                                                                  │
│  📊 OVERVIEW                                                     │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐            │
│  │Schedule │Duration │Title    │Top Tag  │Consist. │            │
│  │  12/mo  │ 19m12s  │ 58 char │62% viral│  65/100 │            │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘            │
│                                                                  │
│  🧠 TONE DNA                                                     │
│  • Persona: "Grounded empathetic financial mentor"               │
│  • Word density: 238 WPM                                        │
│  • Emotion: 35% Empathy · 25% Curiosity · 20% Authority ...     │
│                                                                  │
│  🎯 HOOK TYPES                                                   │
│  • Experiential mirror (60%)                                    │
│  • Alarming statistic (20%)                                     │
│  • Contrarian challenge (20%)                                   │
│                                                                  │
│  📐 STRUCTURAL FORMULA (9 steps)                                │
│  ① Opening Question → ② Problem Statement → ③ ... → ⑨ CTA       │
│                                                                  │
│  💡 HOW TO MIMIC THIS TONE (11 rules)                           │
│  1. OPEN WITH EMOTIONAL MIRROR                                  │
│  2. VALIDATE BEFORE YOU EDUCATE                                 │
│  ...                                                            │
│                                                                  │
│  🕵️ HIDDEN INSIGHTS (7)                                         │
│  ⭐ Tag "tài chính cá nhân" xuất hiện 62% viral                 │
│  ⚠️ Consistency 65/100 — đăng chưa đều                          │
│  ...                                                            │
│                                                                  │
│  🎨 BRAND ASSETS                                                 │
│  About: Tài chính không chỉ là con số...                       │
│  Slogans: "Tài chính đơn giản, cuộc sống phong phú"            │
│  Keywords: [tài chính cá nhân] [kiếm tiền] ...                  │
│                                                                  │
│  🚀 UNTAPPED OPPORTUNITIES (6)                                   │
│  ⭐⭐⭐⭐⭐ Tại Sao 9/10 Người Việt Vẫn Mắc Nợ Mỗi Cuối Tháng?  │
│  ⭐⭐⭐⭐ 6 Quy Tắc Đơn Giản Giúp Người Trẻ Việt Tích Lũy...    │
│  ...                                                            │
│                                                                  │
│  [Export PDF]  [Export JSON]  [Refresh Opportunities]            │
└────────────────────────────────────────────────────────────────┘
```

```typescript
// apps/web/app/(app)/blueprint/[id]/report/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { DeepAnalysisReport } from '@/lib/types';

export default function BlueprintReport({ params }: { params: { id: string } }) {
  const [report, setReport] = useState<DeepAnalysisReport | null>(null);

  useEffect(() => {
    fetch(`/api/assistants/${params.id}/report`)
      .then(r => r.json())
      .then(setReport);
  }, [params.id]);

  if (!report) return <Skeleton />;

  return (
    <div className="container mx-auto py-8 space-y-8">
      <OverviewCards metadata={report.metadata} />
      <ToneDNA pacing={report.pacing_profile} emotion={report.emotional_signature} />
      <HookCategories data={report.hook_categories} />
      <StructuralFormula steps={report.structural_formula.steps} />
      <MimicToneRules rules={report.mimic_tone_rules.rules} />
      <HiddenInsights insights={report.hidden_insights} />
      <BrandAssets assets={report.brand_assets} />
      <UntappedOpportunities opportunities={opportunities} />
    </div>
  );
}
```

### 10e.16. Chi phí bổ sung cho Deep Analysis

| Step | AI call? | Cost ước tính (GPT-4o) |
|------|----------|------------------------|
| Metadata + Tags + Hidden Insights | ❌ (deterministic) | $0 |
| Pacing + Emotional Signature | 1 call | ~$0.05 |
| Hook Categories | 1 call | ~$0.05 |
| Structural Formula | 1 call | ~$0.05 |
| Viral Topics Formula | 1 call | ~$0.05 |
| Mimic Tone (11 rules) | 1 call | ~$0.08 |
| Brand Assets | 1 call | ~$0.05 |
| Untapped Opportunities | 1 call | ~$0.10 |
| **Total / 1 report** | **7 calls** | **~$0.43 / report** |

**Credit cost:** 8 credits / report (Free tier: 2 lần/tháng; Pro: 20 lần/tháng).

### 10e.17. Tích hợp với các power features khác (§10d)

| Power feature | Cách dùng Deep Analysis |
|---------------|-------------------------|
| **Write Scripts** | Inject `mimic_tone_rules` + `structural_formula` + RAG chunks vào SCRIPT_GEN_PROMPT |
| **Generate Titles** | Dùng `viral_topics_formula` để auto-fill template + chọn formula match nhất |
| **Generate Thumbnails** | Dùng `brand_assets` (slogans, color palette) để build thumbnail prompt |
| **Bend Niche** | Dùng `mimic_tone_rules.rules` + `structural_formula` (style chỉ) |
| **Scan Viral Videos** | Kết hợp với `hidden_insights` để highlight "tại sao viral" |

→ Deep Analysis là **single source of truth** mà mọi power feature khác consume.

---

## 11. Prompt Templates

> Lưu trong `apps/worker/prompts/*.py` làm Python string constant.

### 11.1. Style DNA Extraction Prompt

```python
STYLE_DNA_PROMPT = """You are a writing style analyst.

I will give you 5 transcripts from a YouTube channel. Analyze the WRITING STYLE (not content).
Return a JSON object with this EXACT schema:

{{
  "hook_patterns": ["<pattern1>", "<pattern2>", ...],         // 3-5 hook structures used
  "vocabulary_tier": "casual" | "conversational" | "formal" | "academic",
  "avg_sentence_length": <int between 3-50>,
  "pacing": "slow" | "medium" | "fast",
  "signature_phrases": ["<phrase1>", ...],                    // 5-10 phrases they reuse
  "rhetorical_devices": ["<device1>", ...],                   // e.g. "rhetorical questions", "rule of three"
  "tone_keywords": ["<adjective>", ...],                      // e.g. "humorous", "authoritative"
  "example_hooks": ["<first sentence of video 1>", ...]       // 5 examples
}}

Transcripts:
{transcripts}

Return ONLY the JSON. No markdown. No commentary."""
```

### 11.2. Script Generation Prompt

```python
SCRIPT_GEN_PROMPT = """You are a YouTube scriptwriter who mimics a specific style.

STYLE PROFILE (you MUST follow strictly):
{style_dna_json}

TOPIC: {topic}

RULES:
- Hook (first 30s): use one of the patterns from hook_patterns.
- Target length: ~{target_minutes} minutes spoken at 150 wpm.
- Maintain the vocabulary_tier and pacing above.
- Include signature_phrases at least twice.
- Include a CTA near the end.

OUTPUT: the full script as plain text. No markdown. No scene numbers."""
```

### 11.3. Scene Breakdown Prompt

```python
SCENE_BREAKDOWN_PROMPT = """You are a film editor breaking a script into scenes for B-roll footage.

SCRIPT:
{script}

VISUAL STYLE: {style_tone}

RULES:
- Each scene = 4 to 8 seconds of narration.
- Output a JSON ARRAY (not object). Order matters.
- Each scene MUST have:
  - scene_id: integer starting at 1
  - text: exact narration text from script
  - estimated_duration: float seconds (words / 2.5)
  - visual_context: 1 sentence describing the visual
  - search_keyword: 1-3 word English search term (Pexels-friendly)
  - search_keywords_alt: 2 alternative terms
  - asset_type_needed: "video" or "image"

Return ONLY the JSON array. No markdown. No commentary.

Example (do NOT copy):
[
  {{"scene_id":1,"text":"...","estimated_duration":5.2,"visual_context":"...","search_keyword":"...","search_keywords_alt":["...", "..."],"asset_type_needed":"video"}},
  ...
]"""
```

### 11.4. 🆕 Channel X-Ray Prompt *(DNA_plan.md §Giai đoạn 2)*

```python
XRAY_PROMPT = """You are a YouTube channel strategist performing an X-Ray analysis.

Given 5 transcripts from a channel, output JSON:

{{
  "niche": "<short label>",
  "audience_persona": {{
    "age_range": "e.g. 18-34",
    "primary_interest": "<...>",
    "pain_points": ["...", "..."],
    "aspirations": ["...", "..."]
  }},
  "emotional_pacing_curve": [
    {{"phase":"hook","emotion":"curiosity","intensity":9}},
    {{"phase":"setup","emotion":"fascination","intensity":7}},
    {{"phase":"buildup","emotion":"tension","intensity":8}},
    {{"phase":"payoff","emotion":"satisfaction","intensity":10}},
    {{"phase":"cta","emotion":"urgency","intensity":6}}
  ],
  "retention_techniques": [
    "open loops", "pattern interrupts", "controversy hooks", "..."
  ],
  "thumbnail_patterns": ["...", "..."],
  "title_formulas": ["How X without Y", "The TRUTH about Z", "..."]
}}

Transcripts:
{transcripts}

Return ONLY the JSON."""
```

### 11.5. 🆕 Thumbnail Analysis Prompt *(State 8)*

```python
THUMBNAIL_ANALYSIS_PROMPT = """You are a YouTube thumbnail designer.

You will be shown {n} thumbnail images from a successful channel.
Analyze recurring patterns and return JSON:

{{
  "color_palette": ["<hex>", "<hex>", "..."],
  "dominant_layouts": [
    "face left + text right",
    "split diagonal",
    "..."
  ],
  "text_overlay_style": {{
    "typical_word_count": 3,
    "font_style": "bold sans-serif",
    "common_words": ["THE TRUTH", "WHY", "HOW"]
  }},
  "face_patterns": {{
    "expression_intensity": "high",
    "eye_contact_with_camera": true,
    "common_gaze_direction": "direct"
  }},
  "background_patterns": ["solid bright", "gradient", "blurred photo"],
  "clickbait_score_avg": 7,
  "emotional_triggers": ["curiosity", "fear", "outrage"],
  "reusable_template": "<a one-paragraph description of the master template>"
}}"""
```

### 11.6. 🆕 Script Refine Prompt *(State 12)*

Xem §10c.4 — `REFINE_SCRIPT_PROMPT`.

### 11.7. 🆕 Negative Image Prompt Builder *(State 11, optional)*

Nếu sau này cho phép user chọn "AI gen B-roll" thay vì Pexels, cần prompt âm:

```python
NEGATIVE_IMAGE_PROMPT = """Given the following image prompt, generate a NEGATIVE prompt
listing things to AVOID in image generation:

Original: {image_prompt}

Negative prompt should exclude:
- Generic stock photo look
- Obvious AI artifacts (extra fingers, warped text, melted objects)
- Watermarks, logos of real brands
- Cluttered backgrounds
- Low quality, blurry
- Overly saturated colors

Return only the negative prompt string."""
```

---

## 12. JSON Schema chuẩn

### 12.1. `style_dna_profile`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["hook_patterns", "vocabulary_tier", "avg_sentence_length", "pacing",
               "signature_phrases", "rhetorical_devices", "tone_keywords", "example_hooks"],
  "additionalProperties": false,
  "properties": {
    "hook_patterns":         { "type": "array", "minItems": 3, "maxItems": 5, "items": { "type": "string", "minLength": 10 }},
    "vocabulary_tier":       { "enum": ["casual", "conversational", "formal", "academic"] },
    "avg_sentence_length":   { "type": "integer", "minimum": 3, "maximum": 50 },
    "pacing":                { "enum": ["slow", "medium", "fast"] },
    "signature_phrases":     { "type": "array", "minItems": 3, "maxItems": 10, "items": { "type": "string" }},
    "rhetorical_devices":    { "type": "array", "items": { "type": "string" }},
    "tone_keywords":         { "type": "array", "minItems": 3, "items": { "type": "string" }},
    "example_hooks":         { "type": "array", "minItems": 1, "maxItems": 5, "items": { "type": "string", "minLength": 10 }}
  }
}
```

### 12.2. `scenes_data` (array of Scene)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["scene_id", "text", "estimated_duration", "visual_context", "search_keyword", "asset_type_needed", "asset_status"],
    "additionalProperties": false,
    "properties": {
      "scene_id":              { "type": "integer", "minimum": 1 },
      "text":                  { "type": "string", "minLength": 1 },
      "estimated_duration":    { "type": "number", "exclusiveMinimum": 0 },
      "visual_context":        { "type": "string", "minLength": 5 },
      "search_keyword":        { "type": "string", "minLength": 1 },
      "search_keywords_alt":   { "type": "array", "maxItems": 5, "items": { "type": "string" }},
      "asset_type_needed":     { "enum": ["video", "image"] },
      "asset_status":          { "enum": ["pending", "fetched", "no_result", "fallback_image"] },
      "asset": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type":          { "enum": ["video", "image"] },
          "download_url":  { "type": "string", "format": "uri" },
          "thumbnail_url": { "type": "string", "format": "uri" },
          "duration_sec":  { "type": "number" },
          "width":         { "type": "integer" },
          "height":        { "type": "integer" },
          "provider":      { "enum": ["pexels", "pixabay", "unsplash", "ai_generated"] },
          "license":       { "type": "string" },
          "fetched_at":    { "type": "string", "format": "date-time" }
        }
      }
    }
  }
}
```

### 12.3. 🆕 `xray_profile` *(từ DNA_plan.md)*

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["niche", "audience_persona", "emotional_pacing_curve", "retention_techniques", "thumbnail_patterns", "title_formulas"],
  "additionalProperties": false,
  "properties": {
    "niche":               { "type": "string", "minLength": 3 },
    "audience_persona": {
      "type": "object",
      "required": ["age_range", "primary_interest", "pain_points", "aspirations"],
      "properties": {
        "age_range":       { "type": "string" },
        "primary_interest":{ "type": "string" },
        "pain_points":     { "type": "array", "minItems": 1, "items": { "type": "string" }},
        "aspirations":     { "type": "array", "minItems": 1, "items": { "type": "string" }}
      }
    },
    "emotional_pacing_curve": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": ["phase", "emotion", "intensity"],
        "properties": {
          "phase":     { "enum": ["hook", "setup", "buildup", "payoff", "cta", "transition"] },
          "emotion":   { "type": "string" },
          "intensity": { "type": "integer", "minimum": 1, "maximum": 10 }
        }
      }
    },
    "retention_techniques":  { "type": "array", "minItems": 1, "items": { "type": "string" }},
    "thumbnail_patterns":    { "type": "array", "items": { "type": "string" }},
    "title_formulas":        { "type": "array", "items": { "type": "string" }}
  }
}
```

### 12.4. 🆕 `thumbnail_profile` *(GPT-4o vision output)*

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["color_palette", "dominant_layouts", "text_overlay_style"],
  "additionalProperties": false,
  "properties": {
    "color_palette":       { "type": "array", "items": { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$" }},
    "dominant_layouts":    { "type": "array", "items": { "type": "string" }},
    "text_overlay_style": {
      "type": "object",
      "required": ["typical_word_count", "font_style"],
      "properties": {
        "typical_word_count": { "type": "integer", "minimum": 0, "maximum": 10 },
        "font_style":         { "type": "string" },
        "common_words":       { "type": "array", "items": { "type": "string" }}
      }
    },
    "face_patterns": {
      "type": "object",
      "properties": {
        "expression_intensity":  { "enum": ["low", "medium", "high", "extreme"] },
        "eye_contact_with_camera":{ "type": "boolean" },
        "common_gaze_direction": { "type": "string" }
      }
    },
    "background_patterns":   { "type": "array", "items": { "type": "string" }},
    "clickbait_score_avg":   { "type": "integer", "minimum": 1, "maximum": 10 },
    "emotional_triggers":    { "type": "array", "items": { "type": "string" }},
    "reusable_template":     { "type": "string", "minLength": 50 }
  }
}
```

### 12.5. 🆕 `style_dna_profile_v2` *(3-layer mở rộng)*

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["writing_style", "structure", "retention"],
  "additionalProperties": false,
  "properties": {
    "writing_style": {
      "type": "object",
      "required": ["hook_patterns", "vocabulary_tier", "avg_sentence_length", "pacing",
                   "signature_phrases", "rhetorical_devices", "tone_keywords", "example_hooks"],
      "properties": {
        "hook_patterns":       { "type": "array", "minItems": 3, "maxItems": 5, "items": { "type": "string" }},
        "vocabulary_tier":     { "enum": ["casual", "conversational", "formal", "academic"] },
        "avg_sentence_length": { "type": "integer", "minimum": 3, "maximum": 50 },
        "pacing":              { "enum": ["slow", "medium", "fast"] },
        "signature_phrases":   { "type": "array", "minItems": 3, "items": { "type": "string" }},
        "rhetorical_devices":  { "type": "array", "items": { "type": "string" }},
        "tone_keywords":       { "type": "array", "minItems": 3, "items": { "type": "string" }},
        "example_hooks":       { "type": "array", "minItems": 1, "items": { "type": "string" }}
      }
    },
    "structure": {
      "type": "object",
      "required": ["typical_intro_seconds", "typical_outro_seconds", "sections_per_video",
                   "section_templates", "transition_phrases", "curiosity_gaps_per_minute"],
      "properties": {
        "typical_intro_seconds":     { "type": "integer", "minimum": 5, "maximum": 120 },
        "typical_outro_seconds":     { "type": "integer", "minimum": 5, "maximum": 120 },
        "sections_per_video":        { "type": "integer", "minimum": 1, "maximum": 20 },
        "section_templates":         { "type": "array", "items": { "type": "string" }},
        "transition_phrases":        { "type": "array", "items": { "type": "string" }},
        "curiosity_gaps_per_minute": { "type": "number", "minimum": 0, "maximum": 5 }
      }
    },
    "retention": {
      "type": "object",
      "required": ["open_loop_count_avg", "pattern_interrupt_cadence_sec", "cta_type", "cta_position"],
      "properties": {
        "emotion_curve": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["phase", "emotion", "intensity"],
            "properties": {
              "phase":     { "type": "string" },
              "emotion":   { "type": "string" },
              "intensity": { "type": "integer", "minimum": 1, "maximum": 10 }
            }
          }
        },
        "open_loop_count_avg":           { "type": "integer", "minimum": 0 },
        "pattern_interrupt_cadence_sec":  { "type": "integer", "minimum": 10, "maximum": 600 },
        "cta_type":     { "enum": ["subscribe", "comment", "next_video", "lead_magnet", "custom"] },
        "cta_position": { "enum": ["mid_video", "outro", "both"] }
      }
    }
  }
}
```

---

## 13. Credit Billing — Hold-Commit-Release

### 13.1. Pattern tổng quát

```
[Tạo Job]
   │
   ├─ Kiểm tra: credits_available >= amount_needed
   ├─ Kiểm tra: concurrent_jobs < max_concurrent_jobs
   │
   ├─ BEGIN TX:
   │   UPDATE users SET credits_held = credits_held + amount
   │   INSERT INTO credit_transactions (type='hold', amount=-amount, ...)
   │   INSERT INTO jobs (status='pending', credits_held=amount)
   │
   └─ Trả về job_id cho client

[Job chạy xong — SUCCESS]
   │
   ├─ BEGIN TX:
   │   UPDATE users SET credits = credits - amount, credits_held = credits_held - amount
   │   INSERT INTO credit_transactions (type='commit', amount=-amount, ...)
   │   UPDATE jobs SET status='completed', credits_charged=amount
   │

[Job chạy xong — FAIL]
   │
   ├─ BEGIN TX:
   │   UPDATE users SET credits_held = credits_held - amount   (rollback hold)
   │   INSERT INTO credit_transactions (type='release', amount=+amount, ...)
   │   UPDATE jobs SET status='failed'
   │
```

### 13.2. Implementation Python (atomic, dùng Supabase RPC hoặc Postgres function)

```sql
-- supabase/migrations/0002_credit_functions.sql

create or replace function public.hold_credit(p_user uuid, p_amount int, p_job uuid, p_reason text)
returns table(success boolean, available int, held int) language plpgsql as $$
declare
  v_avail int;
  v_max_jobs int;
  v_curr_jobs int;
begin
  select credits, max_concurrent_jobs into v_avail, v_max_jobs
    from public.users where id = p_user for update;
  if v_avail is null then return; end if;
  if v_avail < p_amount then
    return query select false, v_avail, (select credits_held from public.users where id = p_user);
    return;
  end if;
  select count(*) into v_curr_jobs from public.jobs
    where user_id = p_user and status in ('pending','running');
  if v_curr_jobs >= v_max_jobs then
    return query select false, v_avail, (select credits_held from public.users where id = p_user);
    return;
  end if;
  update public.users
    set credits = credits - p_amount,
        credits_held = credits_held + p_amount,
        updated_at = now()
    where id = p_user;
  insert into public.credit_transactions(user_id, type, amount, balance_after, held_after, job_id, reason)
    values (p_user, 'hold', -p_amount, v_avail - p_amount, (v_avail - p_amount) + p_amount, p_job, p_reason);
  return query select true, v_avail - p_amount, (v_avail - p_amount) + p_amount;
end; $$;

create or replace function public.commit_credit(p_job uuid)
returns void language plpgsql as $$
declare v_user uuid; v_amount int;
begin
  select user_id, credits_held into v_user, v_amount from public.jobs where id = p_job for update;
  if v_user is null then return; end if;
  update public.users
    set credits_held = credits_held - v_amount,
        updated_at = now()
    where id = v_user;
  update public.jobs set credits_charged = v_amount where id = p_job;
  insert into public.credit_transactions(user_id, type, amount, balance_after, held_after, job_id, reason)
    select v_user, 'commit', -v_amount,
           (select credits from public.users where id = v_user),
           (select credits_held from public.users where id = v_user),
           p_job, 'job_completed';
end; $$;

create or replace function public.release_credit(p_job uuid, p_reason text)
returns void language plpgsql as $$
declare v_user uuid; v_amount int;
begin
  select user_id, credits_held into v_user, v_amount from public.jobs where id = p_job for update;
  if v_user is null or v_amount = 0 then return; end if;
  update public.users
    set credits = credits + v_amount,
        credits_held = credits_held - v_amount,
        updated_at = now()
    where id = v_user;
  insert into public.credit_transactions(user_id, type, amount, balance_after, held_after, job_id, reason)
    select v_user, 'release', v_amount,
           (select credits from public.users where id = v_user),
           (select credits_held from public.users where id = v_user),
           p_job, p_reason;
  update public.jobs set credits_held = 0 where id = p_job;
end; $$;
```

### 13.3. Khi nào áp dụng từng action

| Trường hợp | Action |
|------------|--------|
| User tạo job | `hold_credit` |
| Worker hoàn thành không lỗi | `commit_credit` |
| Worker fail (sau khi retry hết) | `release_credit` |
| User cancel job đang pending/running | `release_credit` |
| User mua gói / admin bonus | `topup` / `bonus` |

---

## 14. Rate Limiting & Abuse Protection

### 14.1. Per-user rate limit (Redis token bucket)

```python
# apps/api/app/deps/rate_limit.py
RULES = {
    'research_validate':    ('10/hour', '50/day'),
    'assistant_create':     ('5/hour',  '20/day'),
    'project_generate':     ('20/hour', '100/day'),
    'project_break_scenes': ('30/hour', '200/day'),
}
```

Dùng `slowapi` (FastAPI) hoặc tự roll với `redis-py` + Lua script token bucket.

### 14.2. Sanity checks

- `topic` max 500 ký tự.
- `raw_script` max 50,000 ký tự.
- `seed_channel_url` validate regex `youtube.com/(channel/|@|c/)...`.
- Số scenes tối đa mỗi project: 200 (nếu > 200 → bắt user tăng script length tối đa).

### 14.3. Hard caps

- `max_concurrent_jobs` theo tier (đã định nghĩa trong `users` table).
- Pexels API rate limit: 200 req/hour → áp dụng global queue nếu cần.

### 14.4. BYOK option (Phase 2)

- User nhập OpenAI API key vào profile.
- Mã hóa bằng `cryptography.fernet` với key lưu trong env.
- Worker kiểm tra: nếu user có BYOK → dùng key đó, KHÔNG trừ credit cho LLM cost.
- Vẫn trừ credit cho Pexels + YouTube (vì đó là chi phí infra).

---

## 15. Error Handling & Retry Policy

### 15.1. Error format chuẩn

```json
{
  "error": {
    "code": "INSUFFICIENT_CREDIT",
    "message": "You need at least 5 credits to run market research.",
    "details": { "available": 2, "required": 5 }
  }
}
```

| HTTP | Code | Ý nghĩa |
|------|------|----------|
| 400 | `INVALID_INPUT` | Validation fail |
| 401 | `UNAUTHORIZED` | Missing/invalid auth |
| 402 | `INSUFFICIENT_CREDIT` | Hết credit |
| 403 | `RATE_LIMITED` | Quá giới hạn |
| 404 | `NOT_FOUND` | Resource không tồn tại |
| 409 | `JOB_ALREADY_RUNNING` | Đã có job cùng loại đang chạy |
| 422 | `LLM_INVALID_OUTPUT` | LLM trả về JSON sai schema |
| 500 | `INTERNAL_ERROR` | Lỗi server |
| 503 | `PROVIDER_DOWN` | OpenAI/Pexels không phản hồi |

### 15.2. Retry policy (Celery)

| Task | max_retries | retry_backoff | retry_jitter |
|------|-------------|---------------|--------------|
| LLM call (OpenAI) | 3 | exponential (2, 4, 8s) | True |
| YouTube API | 3 | exponential | True |
| Pexels API | 5 | exponential (1, 2, 4, 8, 16s) | True |
| Whisper STT | 2 | fixed 10s | False |

Sau khi retry hết → `release_credit` + `status='failed'` + lưu error message.

### 15.3. Circuit breaker (provider)

- Track `api_usage_logs` 5 phút gần nhất.
- Nếu error rate > 50% trên 10 calls → dừng gọi provider 60s, trả `503 PROVIDER_DOWN`.

---

## 16. Logging & Cost Tracking

### 16.1. Middleware log mọi external call

```python
# apps/worker/utils/cost.py
COST_TABLE = {
    ('openai', 'gpt-4o'): {'input': 2.5/1_000_000, 'output': 10/1_000_000},  # USD/token
    ('openai', 'gpt-4o-mini'): {'input': 0.15/1_000_000, 'output': 0.6/1_000_000},
    ('whisper', 'whisper-1'): {'per_minute': 0.006},
    ('youtube', 'videos.list'): {'per_call': 0},       # free (trong quota)
    ('pexels', 'search'): {'per_call': 0},             # free (trong quota)
    ('pixabay', 'search'): {'per_call': 0},
}

def log_api_call(sb, *, user_id, job_id, provider, model, endpoint,
                 input_tokens=0, output_tokens=0, duration_ms=0,
                 status='success', error=None, metadata=None):
    cost = compute_cost(provider, model, input_tokens, output_tokens, duration_ms)
    sb.table('api_usage_logs').insert({
        'user_id': user_id, 'job_id': job_id,
        'provider': provider, 'model': model, 'endpoint': endpoint,
        'input_tokens': input_tokens, 'output_tokens': output_tokens,
        'duration_ms': duration_ms, 'cost_usd': cost,
        'status': status, 'error': error, 'metadata': metadata or {}
    }).execute()
```

### 16.2. Dashboard nội bộ (Phase 2)

- Query: tổng cost / user / ngày, top users tiêu hao, margin = credits_charged − cost_usd.
- Alert nếu margin âm (user dùng nhiều hơn giá bán).

---

## 17. Bảo mật API Key

### 17.1. Quy tắc

| Key | Lưu ở đâu | Ai đọc được |
|-----|-----------|--------------|
| `OPENAI_API_KEY` | env (Fly.io secret) | **Chỉ Worker** |
| `GEMINI_API_KEY` | env | **Chỉ Worker** |
| `YOUTUBE_API_KEY` | env | Worker + (có thể Next.js nếu muốn SEO) |
| `PEXELS_API_KEY` | env | Worker |
| `PIXABAY_API_KEY` | env | Worker |
| `WHISPER_API_KEY` | env | Worker |
| `SUPABASE_SERVICE_KEY` | env | **Chỉ FastAPI + Worker** |
| `INTERNAL_SECRET` | env | Next.js (BFF) + FastAPI |

### 17.2. Code rule

- FastAPI web layer (`apps/api`) **KHÔNG** import `openai`, `pexels`, `yt_dlp`.
- Mọi LLM call phải đi qua Celery task.
- Validate bằng CI check: tìm `import openai` trong `apps/api/**` → fail build.

---

## 18. Phase Roadmap đã chốt

### Phase 1 (5 tuần) — Core Engine + Module 0-Lite

| Tuần | Sprint | Deliverable |
|------|--------|-------------|
| 1 | S1.1 | Monorepo skeleton, Supabase migrations + RLS, Next.js hello-world |
| 1 | S1.2 | FastAPI skeleton + BFF pattern + Supabase Auth |
| 2 | S2.1 | Celery + Redis + job tracking + Realtime |
| 2 | S2.2 | Credit Hold-Commit-Release + Rate limit |
| 3 | S3.1 | Module 1 — YouTube search + luồng `channels.list → playlistItems.list → videos.list` (3 quota/kênh) |
| 3 | S3.2 | Module 1 — LLM generate 5 titles + UI dashboard |
| 4 | S4.1 | **🆕 Outlier Strength algo (§10b)** + Auto-fetch transcripts (5 video viral nhất) |
| 4 | S4.2 | **🆕 X-Ray analysis (State 4) + Style DNA v2 3-layer (State 5)** + chống AI Slop |
| 5 | S5.1 | Script Generation (State 6) + Refine loop (State 12) + Critical Visual Rule |
| 5 | S5.2 | **🆕 RAG indexing + retrieval (§10c.7)** — pgvector + Few-Shot vào prompt |
| 6 | S6.1 | UI Editor cho script + Apply DNA panel |

### Phase 1.5 (1 tuần) — 🆕 Deep Channel Analysis (OverseerOS-style)

| Tuần | Sprint | Deliverable |
|------|--------|-------------|
| 7 | S7.1 | **🆕 Metadata Analysis (deterministic) — schedule, duration, title length, tags co-occurrence (§10e.3)** |
| 7 | S7.2 | **🆕 Hidden Insights engine — 7 hidden patterns (§10e.4)** + Report UI page |
| 7 | S7.3 | **🆕 Untapped Opportunities gap analysis (§10e.11)** + migrations `0009_deep_analysis.sql` |
| 7 | S7.4 | **🆕 Wire Deep Analysis vào BlueprintProgress (§10e.13)** — update Step 2 |

### Phase 2 (4 tuần) — Scene Breakdown + Thumbnail + Polish

| Tuần | Sprint | Deliverable |
|------|--------|-------------|
| 6 | S6.1 | Module 2 Phase 2.3 — Scene Breakdown (LLM) |
| 6 | S6.2 | Module 2 Phase 2.3 — Pexels/Pixabay fetch + dedup + fallback |
| 7 | S7.1 | UI: scene timeline editor, swap footage, manual upload |
| 7 | S7.2 | Realtime progress UI + toast notifications |
| 8 | S8.1 | **🆕 Thumbnail Analysis (State 7-8) — GPT-4o vision crawl thumbnails** |
| 8 | S8.2 | Stripe billing + multi-tier (free/pro/agency) |
| 9 | S9.1 | BYOK + dashboard nội bộ (cost tracking) |
| 9 | S9.2 | **🆕 State 14 Packaging + Export JSON/Markdown/ZIP** |

### 🆕 Phase 2.5 (2 tuần) — Channel Blueprint UI + 3 Power features mới

| Tuần | Sprint | Deliverable |
|------|--------|-------------|
| 10 | S10.1 | **🆕 BlueprintProgress component + 8-step timeline (§10d.2)** |
| 10 | S10.2 | **🆕 Feature #3: Channel-Specific Title Generation (§10d.5)** + DB `generated_titles` |
| 11 | S11.1 | **🆕 Feature #4: AI Thumbnail Generation với gpt-image-1 (§10d.6)** + DB `generated_thumbnails` + Supabase Storage policy |
| 11 | S11.2 | **🆕 Feature #6: Bend Niche — cross-niche transfer (§10d.8)** + cột `source_assistant_id` |

### Phase 3 (sau) — Scale

- State 11 Negative Image Prompts + AI gen B-roll (Midjourney / DALL-E)
- State 13 Variations (A/B test tiêu đề + intro)
- TTS / voice clone
- Auto upload to YouTube
- Multi-language script

---

## 19. Prompt đưa cho AI Coding

> Copy nguyên khối này + đính kèm PRD v2 vào Cursor / Cline / Copilot:

```
You are an Expert Full-Stack Developer specializing in Next.js 14 (App Router), FastAPI, Celery, and Supabase.

I have attached a complete PRD v2 for a YouTube AI SaaS product. It integrates:
- 12 unresolved points from v1 review
- YouTube quota-optimized flow (3 quota/channel)
- A 14-state machine from DNA_plan.md (chained LLM calls)
- Outlier Strength algorithm for viral video selection
- Anti-AI-Slop rules + Critical Visual Rule

Your task, IN THIS ORDER:

1. Read the PRD v2 thoroughly. Confirm you understand:
   - Monorepo structure (apps/web, apps/api, apps/worker, packages/shared-types, supabase)
   - BFF pattern (Next.js → FastAPI via X-Internal-Secret)
   - Hold-Commit-Release credit system (§13)
   - YouTube 3-step quota-optimized flow (§9.2, §10b)
   - Three phases of Module 2 + 14-state machine (§10a.1)
   - X-Ray → Style DNA v2 → Script → Scene Breakdown pipeline (§10a.2)
   - Outlier Strength algorithm (§10b)
   - Critical Visual Rule & Anti-AI-Slop (§10c)

2. Create files in this order:
   a) supabase/migrations/0001_init.sql  — full schema from §3 (incl. xray_profile, thumbnail_profile, outlier_videos, style_dna_profile_v2)
   b) supabase/migrations/0002_credit_functions.sql — credit functions from §13.2
   c) supabase/migrations/0003_outlier.sql — outlier column index from §10b.3
   d) supabase/migrations/0004_rag.sql — pgvector + dna_chunks table from §10c.7.2
   e) supabase/migrations/0005_rag_function.sql — match_dna_chunks() SQL function from §10c.7.4
   f) supabase/migrations/0006_titles.sql — generated_titles table from §10d.5
   g) supabase/migrations/0007_thumbnails.sql — generated_thumbnails table from §10d.6
   h) supabase/migrations/0008_bent_projects.sql — add source_assistant_id from §10d.8
   i) supabase/migrations/0009_deep_analysis.sql — deep_analysis_reports + untapped_opportunities tables from §10e.12
   j) supabase/policies/0001_rls.sql — RLS policies from §4
   k) packages/shared-types/py/schemas.py — Pydantic models from §5.4 (incl. StyleDNAProfileV2, ChannelXRay, ThumbnailProfile, OutlierVideo, PacingProfile, EmotionalSignature, HookCategoriesAnalysis, StructuralFormula, MimicToneGuideline, BrandAssets, UntappedOpportunities)
   l) packages/shared-types/ts/schemas.ts — Zod mirror
   m) apps/api/app/main.py + routers/{users,research,assistants,projects,deep_analysis}.py
   n) apps/api/app/deps/{auth,credit,rate_limit}.py
   o) apps/worker/celery_app.py
   p) apps/worker/services/transcript.py — outlier selection + yt transcript (§10b.2)
   q) apps/worker/services/rag_indexer.py — build pgvector index (§10c.7.3)
   r) apps/worker/services/rag_retriever.py — query similar chunks (§10c.7.4)
   s) apps/worker/services/asset_providers.py — Pexels + Pixabay + Unsplash fetch (§10.3, plan3)
   t) apps/worker/services/metadata_analysis.py — schedule, duration, title length, tags co-occurrence (§10e.3)
   u) apps/worker/services/hidden_insights.py — 7 hidden patterns discovery (§10e.4)
   v) apps/worker/tasks/research.py — Market Research flow 4 bước (§9.5)
   w) apps/worker/tasks/style_dna.py — X-Ray + Style DNA v2 + RAG indexing (§10a.2)
   x) apps/worker/tasks/script_gen.py — RAG retrieval + script gen + refine (§10c.7.6)
   y) apps/worker/tasks/scene_breakdown.py — Scene Breakdown + fallback chain (§10.3)
   z) apps/worker/tasks/visual.py — Thumbnail Analysis (GPT-4o vision) (§10a.6)
   aa) apps/worker/tasks/titles.py — Channel-Specific Title Generation (§10d.5)
   bb) apps/worker/tasks/thumbnail_gen.py — AI Thumbnail Generation với gpt-image-1 (§10d.6)
   cc) apps/worker/tasks/bend_niche.py — Cross-Niche Transfer (§10d.8)
   dd) apps/worker/tasks/deep_analysis.py — Deep Analysis orchestrator (7 AI calls song song) (§10e.2)
   ee) apps/worker/tasks/untapped_opportunities.py — Gap analysis (§10e.11)
   ff) apps/worker/prompts/{xray,style_dna,script_gen,refine,scene_breakdown,thumbnail,negative,wpm_emotional,hook_categories,structural_formula,viral_topics,mimic_tone,brand_assets,untapped_opportunities,channel_title}.py
   gg) apps/worker/utils/anti_slop.py — heuristic detector (§10c.5)
   hh) apps/web/app/api/*/route.ts — BFF handlers from §6
   ii) apps/web/app/(app)/research/page.tsx — Module 1 dashboard
   jj) apps/web/app/(app)/blueprint/[id]/report/page.tsx — Deep Analysis Report UI (§10e.15)
   y) apps/web/app/(app)/assistants/page.tsx
   z) apps/web/app/(app)/projects/[id]/page.tsx — scene timeline editor
   aa) apps/web/lib/useJobStatus.ts — Realtime subscription hook

3. For every file, follow the EXACT JSON schemas in §12 and EXACT prompts in §11.
   Do NOT invent new schemas.

4. After scaffolding, run the Supabase migrations locally and confirm the schema applies cleanly.

5. Then write a README.md explaining how to run the dev environment (docker-compose with Redis + Postgres local + Supabase CLI).

Important constraints:
- TypeScript strict mode everywhere.
- Python type hints everywhere (mypy-compatible).
- No `any`, no `# type: ignore` without comment.
- Do NOT add API keys to code — read from env only.
- Do NOT call OpenAI/Pexels directly from FastAPI web layer — always go through Celery.
- Honor the CRITICAL VISUAL RULE in SCRIPT_GEN_PROMPT_V2 — never reference visuals during script generation.
- Honor the AI_SLOP_PHRASES forbidden list in §10c.3 — apply heuristic check before returning scripts.
- Outlier score MUST use compute_outlier_score formula from §10b.1.

Start now.
```

---

## ✅ Checklist xác nhận đã giải quyết 12 điểm mờ

| # | Điểm mờ v1 | Giải pháp trong v2 |
|---|--------------|----------------------|
| 1 | BFF hay Direct call? | **§6 — BFF pattern chốt** |
| 2 | Thiếu bảng jobs/credit_tx/api_usage_logs/plans | **§3 — bổ sung đủ 4 bảng** |
| 3 | Chưa có JSON Schema | **§12 — đầy đủ schema cho style_dna + scenes + xray + thumbnail + style_dna_v2** |
| 4 | Chưa có RLS policy | **§4 — policy template đầy đủ** |
| 5 | Polling vs Realtime | **§7 — chốt Supabase Realtime** |
| 6 | Chưa định nghĩa monorepo | **§2 — Turborepo + pnpm rõ ràng** |
| 7 | Chưa có Prompt template | **§11 — 7 prompt đầy đủ (style_dna + script + scene + xray + thumbnail + refine + negative)** |
| 8 | Chưa có bảng giá credit | **§8.2 — bảng giá Phase 1** |
| 9 | Chưa có Rate limit | **§14 — rules + token bucket + sanity check** |
| 10 | Transcript strategy? | **§10.1 — youtube-transcript-api → yt-dlp+Whisper** |
| 11 | Pexels fallback? | **§10.3 Bước B — keyword alt → Pixabay → no_result** |
| 12 | Module 0-Lite? | **§8.1 — đã chốt scope lite/full** |
| Bonus | Hold-Commit-Release | **§13 — pattern + SQL functions** |
| Bonus | YouTube quota | **§9.2 + §10.1 — dùng luồng 3 quota/kênh** |
| Bonus | API key security | **§17 — separation web/worker** |

## ✅ Checklist tích hợp từ `DNA_plan.md` (MỚI)

| # | Nội dung trong DNA_plan.md | Đã tích hợp vào v2 |
|---|------------------------------|---------------------|
| 1 | 14 trạng thái state machine | **§10a.1 — bảng mapping 14 state vào Backend** |
| 2 | Xung đột A: Chat prompt vs SaaS | **§10a.2 — decouple thành 6 AI call riêng biệt** |
| 3 | Xung đột B: User phải upload transcript | **§10.1 + §10b — auto-fetch top outlier transcripts** |
| 4 | Xung đột C: Image prompts → B-roll keywords | **§11.3 — scene breakdown dùng Pexels keyword** |
| 5 | State 4 Channel X-Ray | **§10a.3 — XRAY_PROMPT + §12.3 schema** |
| 6 | State 5 Style DNA (3-layer) | **§10a.4 — StyleDNAProfileV2 + §12.5 schema** |
| 7 | State 7-8 Thumbnail Analysis | **§10a.6 + §11.5 — GPT-4o vision + THUMBNAIL_ANALYSIS_PROMPT** |
| 8 | State 11 Negative Prompts | **§11.7 — NEGATIVE_IMAGE_PROMPT (Phase 3)** |
| 9 | State 12 Refine loop | **§10c.4 + §10c.6 — REFINE_SCRIPT_PROMPT + quality_gate** |
| 10 | State 13 Variations | **§18 Phase 3 — A/B test variations** |
| 11 | State 14 Đóng gói | **§10a.7 — export JSON/Markdown/ZIP** |
| 12 | Outlier Strength algorithm | **§10b — compute_outlier_score + freshness_decay** |
| 13 | Critical Visual Rule | **§10c.1-10c.3 — chèn rule vào SCRIPT_GEN_PROMPT_V2** |
| 14 | Anti-AI-Slop rules | **§10c.3-10c.5 — forbidden phrases list + heuristic detector** |
| 15 | Đề xuất fabric/danielmiessler | **§1 Tech Stack — không dùng fabric (tự build cho SaaS)** |

## ✅ Checklist tích hợp từ `plan2.md` (MỚI)

| # | Nội dung trong plan2.md | Đã tích hợp vào v2 |
|---|--------------------------|---------------------|
| 1 | Flow 4 bước validate ngách | **§9.3 — Search → Videos.list → Channels.list → Top 10** |
| 2 | Ngưỡng validation | **§9.2 — giữ 5M views/30 ngày (mặc định, có thể config per-niche)** |
| 3 | `safe_int()` cho hidden subscriber | **§9.5 — try/except default = 0** |
| 4 | Cache Redis 24-72h theo keyword | **§9.6 — `research:keyword:{lang}:{kw}` với TTL 24h (72h cho evergreen)** |
| 5 | Code Python mẫu | **§9.5 — `validate_and_find_top_channels()` full implementation** |
| 6 | Keyword tiếng Việt → dịch EN | **§9.3 Bước 1 — `relevanceLanguage=language`, dịch qua GPT nếu cần** |
| 7 | Top 10 theo subscriberCount DESC | **§9.3 Bước 4 — sort channels_data theo subscribers** |

## ✅ Checklist tích hợp từ `plan3.md` (MỚI)

| # | Nội dung trong plan3.md | Đã tích hợp vào v2 |
|---|--------------------------|---------------------|
| 1 | Anti-AI-Slop qua Few-Shot + RAG | **§10c.7 — pgvector + text-embedding-3-small + match_dna_chunks()** |
| 2 | Repo `mikiarlo3/ai-copywriter` | **Tham khảo approach; không dùng trực tiếp (tự build để control data)** |
| 3 | Open Footage Pexels (royalty-free) | **§1 Tech Stack + §10.3 fallback chain** |
| 4 | Open Footage Pixabay (bao gồm sound effects) | **§10.3 — Pixabay làm video/image fallback, sound effects cho Phase 3** |
| 5 | 🆕 Open Footage Unsplash (ảnh tĩnh chất lượng cao) | **§10.3 — Unsplash chèn ảnh vào giữa transitions + fallback cuối cho image** |
| 6 | RAG mổ xẻ video viral thành mẫu nhỏ | **§10c.7 — `RecursiveCharacterTextSplitter` chunk 400/80 + pgvector** |
| 7 | Cấm từ "đậm chất AI" | **§10c.3 — ANTI_AI_SLOP_RULES với 13 forbidden phrases** |

## ✅ Checklist Channel Blueprint — 6 Power Features *(MỚI từ screenshot)*

> Phân tích từ UI screenshot "Building Your Channel Blueprint" — màn hình progress 8-step + 6 power buttons.

| # | Feature (UI label) | User-facing description | Backend đã có? | Section trong PRD |
|---|--------------------|--------------------------|----------------|-------------------|
| 1 | **Write scripts in their tone** | "Nhập chủ đề, nhận kịch bản viết bằng văn phong kênh" | ✅ Có sẵn | §10d.3 — script gen + RAG (§10a.5 + §10c.7.6) |
| 2 | **Scan their viral videos** | "Tại sao video viral — copy công thức" | ✅ Có sẵn, cần wrapper giải thích | §10d.4 — X-Ray + Outlier với `explain_viral()` |
| 3 | **🆕 Create titles in their style** | "Tạo tiêu đề theo winning formula riêng của kênh" | ❌ Mới | §10d.5 — `generate_channel_titles()` + DB `generated_titles` |
| 4 | **🆕 Generate thumbnails in their style** | "AI tạo thumbnail theo phong cách thiết kế của kênh" | ⚠️ Đã có analyze (§10a.6), cần thêm generate | §10d.6 — `generate_thumbnail()` với gpt-image-1 + DB `generated_thumbnails` |
| 5 | **Find viral channels in their niche** | "Tìm đối thủ trong cùng ngách" | ✅ Có sẵn | §10d.7 — reuse §9 Module 1 với prefill keyword = niche |
| 6 | **🆕 Bend this channel's niche** | "Giữ format thành công, áp sang ngách mới" | ❌ Mới | §10d.8 — `bend_niche()` cross-niche transfer + cột `source_assistant_id` |

**Tổng hợp implementation effort:**

| Hạng mục | Effort | Ghi chú |
|----------|--------|---------|
| 3 tính năng ĐÃ CÓ (1, 2, 5) | 1 tuần (UI wrappers) | Không cần AI mới, chỉ polish UX |
| 3 tính năng MỚI (3, 4, 6) | 2 tuần | gpt-image-1 + bend niche prompt + DB migrations |
| 8-step Blueprint Progress UI | 3-4 ngày | Realtime subscription + stepper component |
| **Tổng** | **~3 tuần** | = Phase 2.5 trong Roadmap §18 |

---

## ✅ Checklist Deep Channel Analysis — OverseerOS-style *(MỚI từ ana_plan1.md + ana_plan2.md)*

> Phân tích từ workflow của OverseerOS khi áp dụng reverse-engineering sâu cho kênh "Chú Béo Tài Chính".
> App của chúng ta cần tạo ra report y hệt với **13 outputs**.

| # | Output | Trạng thái | Section trong PRD |
|---|--------|------------|-------------------|
| 1 | **Metadata & Performance** — schedule (12/tháng), duration (19m12s), title length (58 chars, 13 words) | 🆕 Mới | §10e.3 — `analyze_metadata()` deterministic |
| 2 | **Tags co-occurrence + viral ratio** (62% viral chứa "tài chính cá nhân") | 🆕 Mới | §10e.3 — `analyze_tags()` + Counter + combinations |
| 3 | **Hidden Insights** (consistency 65/100, optimal duration 18:04-20:28, optimal tag count 6) | 🆕 Mới | §10e.4 — `discover_hidden_insights()` 7 patterns |
| 4 | **Persona Description** ("Grounded empathetic financial mentor") | 🆕 Mới | §10a.4 — `StyleDNAV2.persona` field mới |
| 5 | **Word Density** (238 WPM) | 🆕 Mới | §10e.5 — `PacingProfile.avg_wpm` + `WPM_EMOTIONAL_PROMPT` |
| 6 | **Emotional Signature** (35% Empathy · 25% Curiosity · 20% Authority · 15% Urgency · 5% Mystery) | 🆕 Mới | §10e.5 — `EmotionalSignature` với validator tổng = 100% |
| 7 | **Signature Phrases** ("Tôi biết bạn đang nghĩ gì lúc này", v.v.) | ✅ Có sẵn | §10a.4 — `writing_style.signature_phrases` |
| 8 | **Hook Categories** (experiential_mirror, alarming_statistic, contrarian_challenge, v.v.) | 🆕 Mới | §10e.6 — `HOOK_CATEGORY_PROMPT` + 8 loại enum |
| 9 | **Structural Formula 9 bước** (Opening Question → CTA) | 🆕 Mới | §10e.7 — `STRUCTURAL_FORMULA_PROMPT` |
| 10 | **Viral Topics Formula** (Vì Sao [X]?, [NUMBER] [ITEM] [DESCRIPTION], Tại Sao [X]?) | 🆕 Mới | §10e.8 — `VIRAL_TOPICS_PROMPT` |
| 11 | **How to Mimic Tone (11 nguyên tắc)** (Open with emotional mirror, validate before educate, v.v.) | 🆕 Mới | §10e.9 — `MIMIC_TONE_PROMPT` + 11 rules schema |
| 12 | **Channel Strategy + Brand Assets** (About, Description, Keywords, Slogans, Schedule, Duration, Title length) | 🆕 Mới | §10e.10 — `BRAND_ASSETS_PROMPT` |
| 13 | **Untapped Opportunities** (5-6 gap topics chưa khai thác: "Tại Sao 9/10 Người Việt Vẫn Mắc Nợ...") | 🆕 Mới | §10e.11 — `find_untapped_opportunities()` Celery task |

**Tổng kết:**
- **1/13 output đã có sẵn** (Signature Phrases)
- **12/13 outputs cần xây mới** — chia thành:
  - **Deterministic** (3 outputs: #1, #2, #3): code Python thuần, không tốn AI, ~3 ngày
  - **AI call** (9 outputs: #4, #5, #6, #8, #9, #10, #11, #12, #13): mỗi cái ~0.5 ngày = ~5 ngày
- **Tổng effort**: ~1 tuần = Phase 1.5 trong Roadmap §18

**Implementation detail chính:**
- File `services/metadata_analysis.py` + `services/hidden_insights.py` (deterministic)
- File `prompts/wpm_emotional.py` + `prompts/hook_categories.py` + `prompts/structural_formula.py` + `prompts/viral_topics.py` + `prompts/mimic_tone.py` + `prompts/brand_assets.py` + `prompts/untapped_opportunities.py` (7 prompts)
- File `tasks/deep_analysis.py` orchestrator (gọi 7 AI call song song → aggregate)
- File `tasks/untapped_opportunities.py` Celery task riêng (cho phép refresh on-demand)
- Migration `0009_deep_analysis.sql` cho 2 bảng mới
- UI page `apps/web/app/(app)/blueprint/[id]/report/page.tsx`

---

> **PRD v2 hiện đã tích hợp đầy đủ:**
> - 12 điểm mờ từ `kientruc_bug_tieman.md`
> - Tối ưu YouTube quota từ `plan1.md`
> - Quy trình 14 bước + chống AI Slop từ `DNA_plan.md`
> - Flow validate ngách + cache Redis từ `plan2.md`
> - Few-Shot + RAG + Unsplash từ `plan3.md`
> - **🆕 6 Power Features cho Channel Blueprint từ UI screenshot**
> - **🆕 13 Outputs Deep Channel Analysis OverseerOS-style từ `ana_plan1.md` + `ana_plan2.md`**
>
> **Sẵn sàng đưa vào AI Coding để generate codebase thực tế.**
