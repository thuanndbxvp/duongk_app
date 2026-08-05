# 00 — Shared Context (Context Layer)

> **File này là "single source of truth" cho tất cả sprint.**
> Mỗi sprint sẽ reference lại file này thay vì lặp lại tech stack, naming conventions, etc.

**Sprint file impact (theo PRD v4 Part E):**
- §1 Tech Stack — đã update với v4 chốt: Embedding Router (§2.1), PhoBERT-emotion (§3.2)

---

## 1. Tech Stack (chốt v4)

| Layer | Công nghệ | Ghi chú (v4) |
|-------|-----------|--------------|
| Frontend | Next.js 15 (App Router), React 19, TailwindCSS, shadcn/ui | Server Components ưu tiên |
| Backend REST | Python 3.12 + FastAPI 0.115+ | Pydantic v2 |
| Worker Queue | Celery 5.4 + Redis 7 | Priority queue: high/normal/low |
| Database | Supabase (Postgres 15) + `pgvector` + `pg_cron` | RLS bật toàn bộ |
| Auth | Supabase Auth (email/password Phase 1) | JWT verify tại FastAPI |
| Realtime | Supabase Realtime | Bỏ WebSocket riêng |
| LLM Primary | OpenAI GPT-4o | BYOK optional |
| LLM Fallback | Gemini 1.5 Pro | |
| Embedding Primary | **Cohere embed-multilingual-v3** | Cho VN content (~70%) |
| Embedding EN | OpenAI text-embedding-3-small | Cho EN-only content (≥90% confidence) |
| Embedding Router | `langdetect` + threshold 0.9 | packages/nlp/embedding_router.py |
| Local NLP | underthesea, textstat, VADER | |
| Emotion VN | **wonrax/phobert-base-vietnamese-emotion** (MIT) | Sprint 5 |
| Emotion EN | j-hartmann/emotion-english-distilroberta-base | Apache 2.0 |
| Footage | Pexels → Pixabay → Unsplash → AI-gen | |
| Transcript | youtube-transcript-api → Supadata → yt-dlp+Whisper | Tier-based credit (5/10/25) |
| Trends | pytrends (cache 7d) → SerpAPI Trends | Sprint 6 |
| Observability | Sentry + Prometheus + Grafana + Loki | Bắt buộc Sprint 1 |

**Chi tiết từng layer xem PRD v4:**
- Monorepo: §2 (PRD v3) + `docs/prd_v4.md`
- Database schema: §3 (PRD v3)
- API endpoints: §5 (PRD v3)
- **Embedding Router code: §2.1 PRD v4**
- **Emotion model VN: §3.2 PRD v4**

---

## 2. Monorepo structure

```
/appDK
  /apps
    /web                  # Next.js 15 (BFF pattern)
    /api                  # FastAPI (REST, no LLM key)
    /worker               # Celery worker (LLM key, yt-dlp)
  /packages
    /shared-types         # Pydantic models + auto-gen TypeScript
    /prompts              # LLM prompt templates + test cases
    /formulas             # Pure Python: Appendix A
    /nlp                  # NLP utils + embedding_router + MMR
  /supabase
    /migrations           # SQL migrations (versioned)
      0001_init_users_jobs.sql
      0002_channel_assistants.sql
      0003_market_research_content_projects.sql
      0004_jobs_credit_transactions.sql
      0005_api_usage_logs_quota_ledger.sql
      0006_dna_chunks_cohere_dim.sql   # VECTOR(1024)
      0007_channel_deep_analysis.sql
      0008_rls_policies.sql
      0009_pg_cron_setup.sql
      0010_progress_sub_progress.sql
      0011_partial_commit_credits.sql
    /policies             # RLS policies
    /seed                 # 3-5 reference channels (Chú Béo, ...)
  /scripts
    migrate_openai_to_cohere.py
    seed_reference_channels.py
  /docs
    /sprints              # Folder này
      00_shared_context.md     ← file này
      01_sprint1_foundation.md
      02_sprint2_youtube_collection.md  (coming)
      03_sprint3_deterministic.md       (coming)
      04_sprint4_nlp_dna_script.md      (coming)
```

---

## 3. Naming conventions

### 3.1. Database (Postgres/Supabase)
- **Table names:** `snake_case`, **plural** (`users`, `channel_assistants`, `dna_chunks`)
- **Column names:** `snake_case`, **singular** (`user_id`, `created_at`)
- **Primary key:** `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- **Foreign key:** `<table_singular>_id` (e.g. `assistant_id`, `user_id`)
- **Timestamp:** `created_at`, `updated_at`, `completed_at` (all `TIMESTAMPTZ`)
- **Status enum values:** lowercase, snake (`pending`, `running`, `succeeded`, `failed`, `cancelled`)

### 3.2. TypeScript / Next.js
- **Variables/functions:** `camelCase`
- **Types/Interfaces/Classes:** `PascalCase`
- **Files:** `kebab-case.tsx` cho components, `camelCase.ts` cho utils
- **API routes:** `/api/kebab-case/route.ts`
- **Constants (env, config):** `UPPER_SNAKE_CASE`

### 3.3. Python / FastAPI
- **Modules/Packages:** `snake_case`
- **Classes:** `PascalCase`
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Pydantic models:** `PascalCase` + suffix `Schema`/`Request`/`Response`
- **Celery tasks:** `verb_noun` (e.g. `analyze_channel_dna`, `generate_script`)

### 3.4. SQL migrations
- **Format:** `NNNN_short_description.sql`
- **Counter:** zero-padded 4 digits, incrementing
- **Example:** `0011_partial_commit_credits.sql`

---

## 4. Environment variables (sẽ populate dần qua sprints)

### 4.1. Phase 1 (cần ngay từ Sprint 1)

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...           # cho Next.js (client)
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # cho FastAPI + Worker (bypass RLS)

# CRITICAL (v4.2 D11): JWT secret để verify access_token
# Lấy từ Supabase Dashboard → Project → Settings → API → JWT Secret → Show
SUPABASE_JWT_SECRET=super-secret-jwt-token-from-supabase-dashboard

# FastAPI
API_PORT=8000
API_ENV=development               # development | staging | production

# Worker
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Redis (cache)
REDIS_URL=redis://redis:6379/2

# CORS
CORS_ORIGINS=http://localhost:3000

# Mock credits (Sprint 1 only, replace với Stripe ở Sprint 7)
DEFAULT_USER_CREDITS=1000
```

### 4.2. Phase 2 (sẽ thêm qua Sprint 5+)

```bash
# LLM
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Embeddings
COHERE_API_KEY=...

# Local NLP (HuggingFace token for private models, public cho default)
HF_TOKEN=...

# Trends
SERPAPI_KEY=...

# Footage
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
UNSPLASH_ACCESS_KEY=...

# YouTube (Sprint 2)
YT_KEY_1=AIza...
YT_KEY_2=AIza...
YT_KEY_3=AIza...
YT_KEY_4=AIza...
YT_KEY_5=AIza...

# Observability (Sprint 1)
SENTRY_DSN=...
```

---

## 5. Key patterns (canonical examples)

### 5.1. Supabase client pattern (Next.js + FastAPI)

**Next.js BFF (cookie-based session):**
```typescript
// apps/web/lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export function createSupabaseServerClient() {
  const cookieStore = cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name) { return cookieStore.get(name)?.value; },
        set(name, value, options) { cookieStore.set(name, value, options); },
        remove(name, options) { cookieStore.delete(name, options); },
      },
    }
  );
}
```

**FastAPI (JWT verify + service_role bypass — v4.2 D11):**

> ⚠️ **SECURITY:** Pseudocode trước đây dùng `verify_signature=False` → attacker có thể forge token. Fix bằng `SUPABASE_JWT_SECRET` + PyJWT HS256.

```python
# apps/api/dependencies/supabase.py
from supabase import create_client
from fastapi import Depends, HTTPException, Request
import jwt
import os

# Bắt buộc có trong .env (lấy từ Supabase Dashboard → Settings → API)
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
if not SUPABASE_JWT_SECRET:
    raise RuntimeError(
        'SUPABASE_JWT_SECRET is required. '
        'Get it from Supabase Dashboard → Settings → API → JWT Secret.'
    )

_token_cache: dict[str, dict] = {}


def get_supabase_user(request: Request) -> str:
    """
    Verify JWT từ Next.js BFF và trả về user_id.
    
    Flow: Next.js lấy session cookie → extract access_token → 
    forward sang FastAPI qua Authorization: Bearer <token>.
    FastAPI verify signature bằng SUPABASE_JWT_SECRET.
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail='Missing Bearer token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    token = auth.split(' ', 1)[1].strip()
    
    # Cache để không verify lại trong cùng request
    if token in _token_cache:
        return _token_cache[token]['sub']
    
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience='authenticated',
            options={
                'require': ['exp', 'sub', 'aud'],
                'verify_signature': True,  # ← CRITICAL
                'verify_exp': True,
                'verify_aud': True,
            },
        )
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(401, 'Token missing sub claim')
        _token_cache[token] = payload
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, 'Token expired', headers={'WWW-Authenticate': 'Bearer'})
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f'Invalid token: {e}')


def get_supabase_admin():
    """Service role client — bypasses RLS. Worker only, NEVER expose."""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )


def clear_token_cache():
    """Call ở cuối request để giải phóng memory."""
    _token_cache.clear()
```

> **Xem chi tiết Appendix N.3 (PRD v4.2)** cho test cases + Next.js BFF caller pattern + cách lấy `SUPABASE_JWT_SECRET`.

### 5.2. RLS policy template (canonical)

Mọi table có `user_id` đều dùng pattern này:
```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_<table>"
  ON <table> FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "user_can_insert_own_<table>"
  ON <table> FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_can_update_own_<table>"
  ON <table> FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "user_can_delete_own_<table>"
  ON <table> FOR DELETE
  USING (auth.uid() = user_id);

-- Service role bypass (worker dùng key này)
CREATE POLICY "service_role_bypass_<table>"
  ON <table> FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');
```

### 5.3. Credit hold/commit (SQL template)

```sql
-- HOLD (before enqueue)
BEGIN;
  UPDATE users SET credits = credits - $1
  WHERE id = $2 AND credits >= $1
  RETURNING credits;  -- if NULL → insufficient

  INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after)
  VALUES ($2, $3, 'hold', -$1, (SELECT credits FROM users WHERE id=$2));

  UPDATE jobs SET credits_held = $1 WHERE id = $3;
COMMIT;

-- RELEASE (on failure) — refund
BEGIN;
  UPDATE users SET credits = credits + $1 WHERE id = $2;
  INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after)
  VALUES ($2, $3, 'release', $1, (SELECT credits FROM users WHERE id=$2));
COMMIT;
```

### 5.4. Embedding Router (canonical — §2.1 PRD v4)

```python
from langdetect import detect_langs, DetectorFactory
DetectorFactory.seed = 42  # deterministic

class EmbeddingRouter:
    def embed(self, text: str) -> tuple[list[float], str]:
        model = self._pick_model(text)
        if model == 'openai':
            resp = self.openai.embeddings.create(
                model='text-embedding-3-small', input=text)
            return resp.data[0].embedding, 'openai:text-embedding-3-small'
        else:
            resp = self.cohere.embed(
                texts=[text], model='embed-multilingual-v3.0',
                input_type='search_document')
            return resp.embeddings[0], 'cohere:embed-multilingual-v3.0'
    
    def _pick_model(self, text: str) -> str:
        if len(text.strip()) < 20:
            return 'cohere'
        try:
            langs = detect_langs(text)
            if langs and langs[0].lang == 'en' and langs[0].prob >= 0.9:
                return 'openai'
        except Exception:
            pass
        return 'cohere'
```

---

## 6. Data flow (high-level)

```
┌────────────┐    BFF (cookie session)    ┌────────────┐
│ Browser    │ ──────────────────────────→│ Next.js    │
│            │ ←──────────────────────────│ (web/)     │
└────────────┘                            └─────┬──────┘
                                                │ fetch + JWT
                                                ↓
                                          ┌────────────┐
                                          │ FastAPI    │
                                          │ (api/)     │
                                          └─────┬──────┘
                                                │ enqueue (Celery)
                                                ↓
                            ┌───────────────────┴───────────────────┐
                            ↓                                       ↓
                      ┌──────────┐                            ┌──────────┐
                      │  Redis   │                            │ Supabase │
                      │ (broker) │                            │ (DB+Auth │
                      └────┬─────┘                            │ + Realtime)
                           │                                  └────▲─────┘
                           ↓ enqueue                                │
                      ┌──────────┐                                  │
                      │  Celery  │                                  │
                      │  Worker  │ ──── update jobs.progress ──────┘
                      │ (worker/)│
                      └────┬─────┘
                           │
                           ├──→ YouTube Data API (quota rotation)
                           ├──→ OpenAI / Cohere / Gemini
                           ├──→ Pexels / Pixabay / Unsplash
                           ├──→ pytrends / SerpAPI
                           └──→ yt-dlp / Whisper
```

---

## 7. Testing strategy

### 7.1. Unit tests
- Python: `pytest` trong mỗi package, target coverage ≥ 80% cho `packages/*`, ≥ 60% cho `apps/*`
- TypeScript: `vitest` cho shared logic, không cần test UI components

### 7.2. Integration tests
- End-to-end: `tests/e2e/` chạy với Supabase local + Redis local
- Mỗi sprint có ít nhất 1 happy-path integration test

### 7.3. Regression tests (prompts)
- `tests/prompts/` lưu prerecorded LLM output fixtures
- Mỗi prompt trong Appendix E có ≥ 1 regression test
- Update fixtures khi prompt thay đổi (đánh version)

---

## 8. Sprint roadmap overview

| Sprint | Tuần | Focus | Output |
|--------|------|-------|--------|
| **1 — Foundation** | W1-2 | Monorepo + Supabase + Auth + Credit + Realtime skeleton | User login, có 1000 mock credits, hold/commit hoạt động |
| **2 — YouTube Collection** | W3-4 | YouTube API client + quota rotation + transcript 3-tier | Fetch 1 channel 200 videos + transcripts |
| **3 — Deterministic Analysis** | W5-6 | Outputs #1-4 (#14 thumbnail partial) | Xem được metadata + tags + performance report |
| **4 — NLP DNA + Script Gen** | W7-8 | Outputs #5-11 + Module 3 + RAG + Anti-slop | End-to-end: URL → Analysis → Script → Scenes |
| 5 — Local ML | W9-10 | PhoBERT emotion + Anti-slop LLM validator + Sig phrases | Emotional curve viz |
| 6 — Content Gap | W11-12 | Module 2E + pytrends integration | Untapped Opportunities output |
| 7 — Module 0 Full | W13 | OAuth + Stripe + Multi-tier + Admin | Production-grade auth + payment |
| 8 — Vision + Polish | W14 | Thumbnail Analysis full + Content Calendar + Export PDF | Public beta launch |

---

## 9. References

- **PRD v3:** `docs/prd_v3.md` — base design (1652 lines)
- **PRD v4:** `docs/prd_v4.md` — patches (12 fixes, 3 new appendices K/L/M)
- **PRD v3 Review:** `docs/prd_v3_review.md` — original 12 issues
- **Appendix A (Formulas):** PRD v3 §945-1134
- **Appendix K (Progress):** PRD v4 §535-674
- **Appendix L (Anti-Slop):** PRD v4 §678-787
- **Appendix M (RAG SQL):** PRD v4 §791-932

---

> **Bắt đầu từ đây** → xem `01_sprint1_foundation.md` để bắt tay code ngay.
