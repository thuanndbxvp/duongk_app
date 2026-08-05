# PRD v3 — YouTube AI SaaS (Channel Cloning Platform)

> **Bản kế thừa & mở rộng:** `kientruc.md` (v1) → `prd_v2.md` → **v3 (bản này)**
> **Bổ sung dựa trên:** `ana_plan1.md`, `ana_plan2.md` (OverseerOS-style 13 outputs, "Chú Béo Tài Chính" case)
> **Trọng tâm v3:** Đóng kín 3 khâu yếu — (A) YouTube Data Collection, (B) Style/Tone DNA NLP Analysis, (C) Metadata/Tags/Ý tưởng — kèm 9 Appendix để AI Coding (Cursor/Cline) có thể sinh code chạy được ~95% mà không cần đoán thêm.
> **Ngày phát hành:** 2026-08

---

## 0. MỤC LỤC

**PART I — Foundation (giữ từ v2, có bổ sung)**
1. Tech Stack đã chốt
2. Monorepo & Kiến trúc tổng thể
3. Database Schema đầy đủ (bổ sung 6 bảng mới)
4. RLS Policy Template
5. API Endpoints & Contract
6. Auth & BFF Pattern
7. Realtime & Job Tracking
8. Module 0-Lite (User, Credit, Tier)
9. Credit System — Hold/Commit/Release

**PART II — Core Analysis Pipeline (mới, thay Module 1-2 cũ)**
10. Pipeline tổng thể "Channel Cloning" (13 outputs)
11. Module 1 — Discovery & Niche Validation
12. Module 2A — YouTube Data Collection Engine
13. Module 2B — Metadata & Performance Analysis (Deterministic)
14. Module 2C — NLP Style DNA Analysis (Hybrid: Code + LLM + Local ML)
15. Module 2D — Structural & Hook Decoding
16. Module 2E — Content Gap & Idea Generation
17. Module 3 — Script Generation + Scene Breakdown (giữ từ v2)

**PART III — Appendices (mới, bắt buộc cho AI Coding)**
- Appendix A — Formulas & Thresholds Sheet
- Appendix B — YouTube Quota Budget & Key Rotation
- Appendix C — External API Fallback Matrix
- Appendix D — Deterministic vs LLM vs Local-ML Task Matrix
- Appendix E — Prompt Templates + Test Suite
- Appendix F — Vietnamese-specific Config
- Appendix G — 13 Outputs Dependency DAG
- Appendix H — Cost Model per Action (Credit Pricing)
- Appendix I — Legal / ToS Compliance
- Appendix J — Sprint Roadmap (Phase 1 → Phase 2)

---

# PART I — FOUNDATION

## 1. Tech Stack đã chốt

| Layer | Chốt v3 | Ghi chú |
|---|---|---|
| Frontend | Next.js 15 (App Router), React 19, TailwindCSS, shadcn/ui | Server Components ưu tiên |
| Backend REST | Python 3.12 + FastAPI 0.115+ | Pydantic v2 |
| Worker Queue | Celery 5.4 + Redis 7 | Priority queue: high/normal/low |
| Database | Supabase (Postgres 15) + `pgvector` + `pg_cron` | RLS bật toàn bộ |
| Auth | Supabase Auth (email/password Phase 1, OAuth Phase 2) | JWT verify tại FastAPI |
| Realtime | Supabase Realtime (subscribe `content_projects.status`, `jobs.progress`) | **Bỏ WebSocket riêng** |
| LLM | OpenAI GPT-4o (primary) + Gemini 1.5 Pro (fallback) | BYOK optional cho power user |
| Embedding | `text-embedding-3-small` (default) + `Cohere embed-multilingual-v3` (VN) | Auto-detect language |
| Local NLP | `underthesea` (VN tokenizer), `textstat`, `VADER`, `j-hartmann/emotion-english-distilroberta-base` | Chạy trong Worker |
| Footage | Pexels → Pixabay → Unsplash → AI-gen (fallback chain) | Xem Appendix C |
| Transcript | `youtube-transcript-api` → Supadata API → `yt-dlp` + Whisper | Xem Appendix C |
| Trends signal | `pytrends` (unofficial free) → SerpAPI Trends (paid fallback) | **Bổ sung v3** |
| Observability | Sentry + Prometheus + Grafana + Loki | Bắt buộc từ Sprint 1 |

**Bỏ khỏi v3:** SocialBlade scraping (rủi ro pháp lý, dời sang backlog).

---

## 2. Monorepo & Kiến trúc tổng thể

```
/apps
  /web                     # Next.js 15
  /api                     # FastAPI (REST layer, no LLM key)
  /worker                  # Celery worker (có LLM key, có yt-dlp)
/packages
  /shared-types            # Pydantic models + auto-gen TypeScript (via datamodel-code-generator)
  /prompts                 # LLM prompt templates + test cases
  /formulas                # Pure Python: metadata/statistics formulas
  /nlp                     # NLP utils: tokenizer, sentiment, readability
/supabase
  /migrations              # SQL migrations (versioned)
  /policies                # RLS policies
  /seed                    # Test data (3-5 reference channels)
/docs
  /appendices              # A → J
```

**Nguyên tắc separation:**
- `api` **không** được import `packages/nlp` hay có OpenAI key trong env — chỉ enqueue job.
- `worker` được đọc key từ Supabase Vault (không hardcode).
- `shared-types` là single source of truth cho JSON contract Pydantic ↔ Zod.

---

## 3. Database Schema đầy đủ

### 3.1 Bảng đã có từ v2 (giữ nguyên, refine)
`users`, `channel_assistants`, `market_research`, `content_projects`.

### 3.2 🆕 6 bảng mới trong v3

#### `jobs` — Track Celery async task
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  task_type TEXT NOT NULL,          -- 'research_validate' | 'dna_extract' | 'script_generate' | 'scene_breakdown' | 'deep_channel_analysis'
  celery_task_id TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | running | succeeded | failed | cancelled
  progress INT DEFAULT 0,           -- 0-100
  input_payload JSONB,
  result_payload JSONB,
  error_message TEXT,
  credits_held INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
```

#### `credit_transactions` — Ledger đầy đủ
```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  action TEXT NOT NULL,             -- 'hold' | 'commit' | 'release' | 'topup' | 'admin_adjust'
  amount INT NOT NULL,              -- signed: negative = deduct
  balance_after INT NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_credit_tx_user ON credit_transactions(user_id, created_at DESC);
```

#### `api_usage_logs` — Cost tracking mọi API call
```sql
CREATE TABLE api_usage_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  provider TEXT NOT NULL,           -- 'openai' | 'gemini' | 'youtube' | 'pexels' | 'pixabay' | 'unsplash' | 'pytrends' | 'whisper' | 'supadata'
  operation TEXT NOT NULL,          -- 'chat.completions' | 'embeddings' | 'search.list' | ...
  input_tokens INT,
  output_tokens INT,
  cost_usd NUMERIC(10,6),
  quota_units INT,                  -- for YouTube API
  api_key_id TEXT,                  -- for rotation tracking
  status_code INT,
  duration_ms INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_usage_provider_date ON api_usage_logs(provider, created_at DESC);
```

#### `quota_ledger` — Real-time YouTube quota tracking
```sql
CREATE TABLE quota_ledger (
  id BIGSERIAL PRIMARY KEY,
  api_key_id TEXT NOT NULL,
  date DATE NOT NULL,
  units_used INT NOT NULL DEFAULT 0,
  units_limit INT NOT NULL DEFAULT 10000,
  UNIQUE(api_key_id, date)
);
```

#### `dna_chunks` — RAG store cho Anti-AI-Slop
```sql
CREATE TABLE dna_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  source_video_id TEXT NOT NULL,
  section TEXT NOT NULL,            -- 'hook' | 'body' | 'analogy' | 'cta' | 'transition'
  chunk_index INT NOT NULL,
  text_content TEXT NOT NULL,
  word_count INT,
  timestamp_start_sec NUMERIC,
  timestamp_end_sec NUMERIC,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dna_chunks_asst ON dna_chunks(assistant_id);
CREATE INDEX idx_dna_chunks_embedding ON dna_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### `channel_deep_analysis` — Lưu 13 outputs OverseerOS-style
```sql
CREATE TABLE channel_deep_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  -- Layer 1: Deterministic outputs (Python-computed)
  metadata_report JSONB,            -- upload freq, duration, title length
  tags_report JSONB,                -- co-occurrence, top tags, saturation
  performance_report JSONB,         -- outlier videos, viral videos
  hidden_insights JSONB,            -- statistical anomalies
  -- Layer 2: NLP outputs (LLM-generated + Local-ML validated)
  tone_dna JSONB,                   -- persona, pacing, emotional_signature
  hook_analysis JSONB,              -- hook types, hook density, extracted hooks
  structural_formula JSONB,         -- 9-step template (or K-step, learned)
  signature_phrases JSONB,          -- {phrase, frequency, section}
  mimic_rules JSONB,                -- 11 nguyên tắc bắt chước
  -- Layer 3: Creative outputs (LLM-generated)
  viral_topics_formula JSONB,       -- title templates with placeholders
  untapped_opportunities JSONB,     -- gap analysis + new ideas
  content_calendar JSONB,           -- suggested schedule
  thumbnail_analysis JSONB,         -- Vision LLM output
  -- Meta
  analysis_version TEXT DEFAULT 'v3.0',
  source_video_ids TEXT[],          -- videos used for analysis
  source_transcript_count INT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. RLS Policy Template

```sql
-- Áp cho MỌI bảng có user_id
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_jobs"
  ON jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "user_can_insert_own_jobs"
  ON jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "service_role_bypass"
  ON jobs FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');
```

**Nguyên tắc:**
- Worker dùng `service_role` key để bypass RLS khi update `jobs.progress`.
- Web layer dùng `anon` + user JWT → RLS enforce.

---

## 5. API Endpoints & Contract

### 5.1 Full endpoint list (v3)

**Users & Credits:**
- `GET /api/users/me`
- `GET /api/users/me/credits/history`
- `POST /api/users/me/byok` — Set custom OpenAI key

**Module 1 — Discovery:**
- `POST /api/research/validate` — Body `{keyword, region_code?, language?}`
- `GET /api/research/{job_id}`
- `GET /api/research/history`

**Module 2 — Channel Analysis:**
- `POST /api/assistants` — Body `{seed_channel_url, name}` → tạo skeleton + trigger deep_analysis job
- `GET /api/assistants`
- `GET /api/assistants/{id}` — trả full skeleton
- `GET /api/assistants/{id}/deep-analysis` — trả 13 outputs
- `POST /api/assistants/{id}/re-analyze` — chạy lại analysis với video mới nhất
- `DELETE /api/assistants/{id}`

**Module 3 — Script:**
- `POST /api/projects/generate` — Body `{topic, assistant_id, target_duration_min?}`
- `GET /api/projects/{id}`
- `PATCH /api/projects/{id}/script` — user edit
- `POST /api/projects/{id}/breakdown` — trigger scene breakdown
- `PATCH /api/projects/{id}/scenes/{scene_id}/asset` — swap footage

**Jobs (general):**
- `GET /api/jobs/{id}`
- `DELETE /api/jobs/{id}` — cancel (release credit)

### 5.2 Contract sync: Pydantic ↔ Zod

Pipeline sinh types:
```
apps/api/models/*.py (Pydantic) 
  ↓ (datamodel-code-generator + custom script)
packages/shared-types/generated/*.ts (Zod schemas)
  ↓ (imported by apps/web)
```

---

## 6. Auth & BFF Pattern

**Chốt: BFF Pattern (không Direct Call).**

```
Browser 
  → Next.js /api/* (Server Component / Route Handler) [attach cookies, verify session]
  → FastAPI /api/* [verify Supabase JWT via /auth/v1/user]
  → Enqueue Celery job → Worker
```

**Lý do BFF:**
- Ẩn FastAPI endpoint khỏi client.
- Rate limit tại Next.js layer trước.
- Cookies-based session, không expose JWT trong browser.

---

## 7. Realtime & Job Tracking

**Chốt: Supabase Realtime, bỏ WebSocket riêng.**

Frontend subscribe:
```ts
supabase.channel(`jobs:${userId}`)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'jobs',
    filter: `user_id=eq.${userId}`
  }, (payload) => {
    // update UI progress bar
  })
  .subscribe();
```

Worker chỉ cần `UPDATE jobs SET progress=... WHERE id=...` → Realtime tự push.

---

## 8. Module 0-Lite (Phase 1 mandatory)

**Có trong Phase 1:**
- Supabase Auth email/password
- Bảng `users` + `credits` (mock 1000 credits/user for testing)
- Middleware verify JWT + attach `user_id` to every FastAPI endpoint
- RLS enforce toàn bộ
- Credit deduction middleware (hold/commit/release)
- Rate limit: 10 req/min per user, 3 concurrent jobs

**Dời sang Phase 2:**
- OAuth Google
- Trang mua credit + Stripe
- Multi-tier (Free/Pro/Agency) với limit khác nhau
- Team/organization support

---

## 9. Credit System — Hold/Commit/Release

**State machine:**
```
[Job created] → HOLD credits  → status=pending
                      ↓
                [Worker starts] → status=running
                      ↓
        ┌─────────────┴─────────────┐
        ✅ Success              ❌ Failure
        COMMIT (finalize)      RELEASE (refund)
        status=succeeded       status=failed
```

**SQL (transactional, atomic):**
```sql
-- HOLD (before enqueue)
BEGIN;
  UPDATE users SET credits = credits - $1 WHERE id = $2 AND credits >= $1;
  -- if 0 rows → throw InsufficientCreditsError
  INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after)
    VALUES ($2, $3, 'hold', -$1, (SELECT credits FROM users WHERE id=$2));
  UPDATE jobs SET credits_held = $1 WHERE id = $3;
COMMIT;

-- COMMIT (on success) — no balance change, only log
INSERT INTO credit_transactions (user_id, job_id, action, amount, ...)
  VALUES ($2, $3, 'commit', 0, ...);

-- RELEASE (on failure) — refund
BEGIN;
  UPDATE users SET credits = credits + $1 WHERE id = $2;
  INSERT INTO credit_transactions ... action='release', amount=+$1;
COMMIT;
```

---

# PART II — CORE ANALYSIS PIPELINE

## 10. Pipeline tổng thể "Channel Cloning" (13 outputs)

Đây là **thay đổi lớn nhất so với v2**. Bản v2 gom hết vào "Phase 2.1 Style DNA Extraction" mập mờ. Bản v3 tách rõ **13 output** với **dependency DAG** (xem Appendix G).

### 13 outputs cụ thể (OverseerOS-style, học từ `ana_plan1.md`, `ana_plan2.md`):

| # | Output | Layer | Tool | Dependency |
|---|--------|-------|------|------------|
| 1 | **Metadata Report** (upload freq, duration, title length) | Deterministic | Python + numpy | Raw video list |
| 2 | **Tags Report** (co-occurrence, top tags, saturation) | Deterministic | Python + Counter | Raw video list |
| 3 | **Performance Report** (viral videos = top-K outliers) | Deterministic | Python + statistics | Raw video list |
| 4 | **Hidden Insights** (statistical anomalies) | Deterministic + LLM interpret | Python stats → LLM narrate | Outputs 1,2,3 |
| 5 | **Persona** (Grounded/Empathetic Mentor…) | LLM | GPT-4o | Transcripts (viral videos) |
| 6 | **Pacing Profile** (WPM, sentence length curve) | Deterministic + Local NLP | Python + underthesea | Transcripts |
| 7 | **Emotional Signature** (%empathy, %curiosity...) | Local ML | RoBERTa emotion model | Transcripts |
| 8 | **Hook Analysis** (types + extracted hooks + density) | LLM + Regex | GPT-4o + regex validator | Transcripts (first 30s each) |
| 9 | **Structural Formula** (9-step or K-step template) | LLM + rule-check | GPT-4o | Transcripts (full) |
| 10 | **Signature Phrases** | Deterministic + LLM | n-gram TF-IDF → LLM label | Transcripts |
| 11 | **Mimic Rules** (11 nguyên tắc) | LLM (constrained) | GPT-4o | Outputs 5-10 |
| 12 | **Viral Topics Formula** (title templates w/ placeholders) | LLM + Clustering | Embedding cluster → LLM | Top-K viral video titles |
| 13 | **Untapped Opportunities** (new ideas) | LLM + Gap Analysis | Embedding gap detection → LLM | Outputs 1,2,12 + Google Trends |

**Ngoài ra (bonus, không đánh số):**
- **Thumbnail Analysis** — GPT-4o Vision phân tích bố cục, màu, biểu cảm face.
- **Content Calendar** — Suggested upload schedule dựa trên Metadata Report.

---

## 11. Module 1 — Discovery & Niche Validation

### 11.1 Input
```json
{
  "keyword": "tài chính cá nhân",
  "region_code": "VN",         // default: VN
  "language": "vi",             // default: vi
  "include_shorts": false       // default: false (long-form only)
}
```

### 11.2 Pipeline (7 steps)

```
Step 1: Normalize keyword (lowercase, trim, remove tone marks optionally)
Step 2: Check Redis cache: search:{normalized}:{region}:{lang}:{shorts}
        → HIT: return cached (age < 24h)
        → MISS: acquire distributed lock (SETNX with 60s TTL)

Step 3: Call youtube.search.list(
          q=keyword, type='video', 
          publishedAfter=now-30d,
          regionCode='VN', relevanceLanguage='vi',
          order='viewCount',        # ← quan trọng, không dùng 'relevance'
          maxResults=50
        )
        # quota: 100 units

Step 4: Extract video_ids → batch call videos.list(id=..., part='statistics,snippet,contentDetails')
        # quota: 1 unit for 50 IDs

Step 5: Filter:
        - Exclude if liveBroadcastContent != 'none'
        - Exclude if duration < 60s (unless include_shorts=true)
        - Exclude if channel < 1000 subs (spam filter)

Step 6: Calculate:
        - total_monthly_views = sum(views)
        - is_viable = (total_monthly_views >= 5_000_000) AND (google_trends_avg_interest >= 30)
        
Step 7: Extract unique channel_ids, batch call channels.list(id=..., part='statistics,snippet')
        # quota: 1 unit for 50 channels

Step 8: [Parallel] Fetch Google Trends for keyword (pytrends, 12-month window)
        → interest_over_time, related_queries

Step 9: LLM → generate 5 title ideas (SCRIPT_TITLE_IDEAS_PROMPT)
Step 10: Cache result 24h + save to market_research table
```

### 11.3 Output schema
```typescript
type MarketResearchResult = {
  keyword: string;
  is_viable: boolean;
  reason?: string;                    // if not viable
  total_monthly_views: number;
  google_trends_interest: number;     // 0-100
  google_trends_trend: 'rising' | 'stable' | 'declining';
  top_channels: Channel[];            // top 10-100
  top_videos: Video[];                // top 50
  suggested_titles: string[];         // 5 ideas
  fetched_at: string;                 // ISO timestamp
  cache_hit: boolean;
};
```

---

## 12. Module 2A — YouTube Data Collection Engine

**Đây là khâu bạn hỏi. Bản v2 nói mơ hồ. Bản v3 định nghĩa cụ thể.**

### 12.1 Ba chế độ collection

| Mode | Trigger | Video count | Purpose |
|------|---------|-------------|---------|
| **Shallow** | Module 1 discovery | 50 | List videos in niche |
| **Medium** | User selects channel to preview | ~50 latest videos of 1 channel | Show channel profile |
| **Deep** | User confirms "Create Assistant" | ~200-500 videos of 1 channel (max 2 years) | Deep analysis + Style DNA |

### 12.2 Deep collection flow (channel → transcripts)

```
Input: seed_channel_url
Step 1: Parse URL → extract channel_id (support @handle, /channel/UC..., /user/, /c/)
        Fallback: search.list(q=handle, type='channel') # quota 100

Step 2: channels.list(id=..., part='snippet,statistics,contentDetails')
        → get uploads_playlist_id
        # quota: 1 unit

Step 3: Paginate playlistItems.list(playlistId=uploads_playlist_id, maxResults=50)
        Loop until 200 videos OR published < 2 years ago
        # quota: 1 unit per 50 items = 4 units for 200 videos

Step 4: Batch videos.list (50 IDs per call)
        part='snippet,statistics,contentDetails,topicDetails,status'
        # quota: 1 unit per 50 videos = 4 units for 200 videos

Step 5: Filter:
        - Exclude Shorts (duration < 60s) if user wants long-form clone
        - Exclude live streams
        - Exclude age-restricted / region-blocked

Step 6: Rank by outlier_strength (see Appendix A, Formula A3)
        → select top-K viral videos (default K=5 for DNA, K=20 for tag analysis)

Step 7: For each of top-K viral videos, fetch transcript:
        Try tier-1: youtube-transcript-api (with residential proxy)
        Fallback tier-2: Supadata API
        Fallback tier-3: yt-dlp download audio → Whisper STT
        See Appendix C.

Step 8: Store raw data in Supabase:
        - youtube_videos_cache table (24h TTL)
        - transcripts table (permanent, keyed by video_id)
```

**Total quota per Deep collection ≈ 10-12 units** (very cheap thanks to batch).

### 12.3 Quota rotation (bắt buộc production)

```python
class YouTubeClient:
    def __init__(self):
        # Load N API keys from env: YT_KEY_1, YT_KEY_2, ...
        self.keys = load_keys()
    
    def get_client(self):
        # Query quota_ledger for today
        # Pick key with min units_used (that has quota left)
        # If ALL keys exhausted → raise QuotaExhaustedError
        # ...

    def call(self, operation, **params):
        client = self.get_client()
        cost = OPERATION_COST[operation]  # search.list=100, videos.list=1, etc.
        try:
            resp = client.execute(**params)
            self.log_usage(client.key_id, cost)
            return resp
        except HttpError as e:
            if e.status == 403 and 'quotaExceeded' in str(e):
                self.mark_key_exhausted(client.key_id)
                return self.call(operation, **params)  # retry with next key
            raise
```

### 12.4 Cache strategy (chi tiết)

| Data | Key pattern | TTL | Invalidation |
|------|-------------|-----|--------------|
| `search.list` results | `yt:search:{sha1(q+region+lang+shorts)}` | 24h | Time-based |
| `videos.list` (per video_id) | `yt:video:{video_id}` | 24h | Time-based + on-demand refresh |
| `channels.list` | `yt:channel:{channel_id}` | 24h | Time-based |
| `playlistItems.list` (uploads) | `yt:uploads:{channel_id}:{page}` | 6h | Time-based (channel posts often) |
| Transcript | Postgres `transcripts` table | Permanent | Never (immutable per video_id) |

**Cache stampede prevention:**
```python
def get_or_fetch(cache_key, fetch_fn):
    val = redis.get(cache_key)
    if val: return val
    lock_key = f"lock:{cache_key}"
    if redis.set(lock_key, "1", nx=True, ex=60):  # got lock
        try:
            val = fetch_fn()
            redis.set(cache_key, val, ex=86400)
            return val
        finally:
            redis.delete(lock_key)
    else:
        # someone else is fetching, wait
        for _ in range(30):
            time.sleep(1)
            val = redis.get(cache_key)
            if val: return val
        raise TimeoutError("Waited too long for cache")
```

---

## 13. Module 2B — Metadata & Performance Analysis (Deterministic)

**Đây là output #1, #2, #3, #4 trong 13 outputs. TOÀN BỘ chạy Python, KHÔNG dùng LLM (trừ bước "narrate insight" cuối).**

### 13.1 Metadata Report (Output #1)

Input: list of ~50-200 videos with `snippet.publishedAt`, `snippet.title`, `contentDetails.duration`.

```python
def analyze_metadata(videos: list) -> dict:
    return {
        "upload_frequency": {
            "videos_per_month": len(videos) / months_covered(videos),
            "avg_gap_days": mean(gaps_between_uploads(videos)),
            "std_gap_days": stdev(gaps_between_uploads(videos)),
            "consistency_score": consistency_score(videos),  # Formula A5
        },
        "duration": {
            "median_seconds": median(durations),
            "optimal_range": (percentile(durations, 25), percentile(durations, 75)),
            "human_readable_median": format_duration(median(durations)),  # e.g. "19:34"
        },
        "title_length": {
            "median_chars": median([len(t) for t in titles]),
            "median_words": median([len(t.split()) for t in titles]),
            "optimal_char_range": (p25, p75),
        },
        "posting_schedule": {
            "top_day_of_week": Counter(dow(videos)).most_common(1),
            "top_hour_utc": Counter(hour(videos)).most_common(1),
            # NOTE: timezone caveat — see Appendix F
        }
    }
```

### 13.2 Tags Report (Output #2)

```python
def analyze_tags(videos: list, viral_threshold_fn) -> dict:
    all_tags = flatten([v.get('snippet', {}).get('tags', []) for v in videos])
    viral_videos = [v for v in videos if viral_threshold_fn(v)]
    viral_tags = flatten([v.get('snippet', {}).get('tags', []) for v in viral_videos])
    
    return {
        "total_unique_tags": len(set(all_tags)),
        "top_tags": Counter(all_tags).most_common(20),
        "viral_tag_ratio": {
            tag: len([v for v in viral_videos if tag in v.tags]) / len(viral_videos)
            for tag in set(viral_tags)
        },  # e.g. {"tài chính cá nhân": 0.62}
        "tag_count_stats": {
            "avg_per_video": mean(tag_counts),
            "optimal_count": mode_of_top_performers(videos),  # Formula A6
        },
        "co_occurrence": top_cooccurring_pairs(videos, top_n=10),  # Formula A7
        "saturation": {
            "balanced": count_where(usage_ratio in [0.1, 0.4]),
            "over_saturated": count_where(usage_ratio > 0.6),
            "under_utilized": count_where(usage_ratio < 0.1),
        }
    }
```

### 13.3 Performance Report (Output #3) — "What is Viral?"

**Định nghĩa "Viral" (chốt v3):**
```
outlier_strength(v) = (v.views - median_views_of_channel) / MAD(views)
is_viral = outlier_strength >= 2.5  AND views_per_sub >= 0.3

# where:
# MAD = Median Absolute Deviation (robust vs stdev)
# views_per_sub = views / subscriberCount at time of analysis
```

Xem chi tiết trong Appendix A, Formula A3.

### 13.4 Hidden Insights (Output #4)

Đây là output "wow-factor" giống OverseerOS. **Bí quyết:** không cho LLM tự "phát hiện", mà bắt LLM **narrate** các finding statistical.

```python
def find_hidden_insights(metadata, tags, performance) -> list[Insight]:
    insights = []
    
    # Insight rule 1: Success formula = duration × tag_count
    long_videos_with_many_tags = [v for v in videos if v.duration_min >= 19 and len(v.tags) >= 10]
    if len(long_videos_with_many_tags) / len(viral_videos) >= 0.4:
        insights.append({
            "type": "success_formula",
            "text_raw": f"{pct}% viral videos combine 19+ min duration with 10+ tags",
            "significance": chi_square_test(...),  # only include if p < 0.05
        })
    
    # Insight rule 2: Word in title
    for word in top_title_words:
        if viral_correlation(word, videos) > 0.5:
            insights.append({
                "type": "title_keyword",
                "text_raw": f"Word '{word}' appears in {pct}% viral titles"
            })
    
    # Insight rule 3-8: ... (see Appendix A)
    
    # Only LLM step: rewrite text_raw → natural Vietnamese narration
    return llm_narrate_insights(insights, prompt=HIDDEN_INSIGHTS_NARRATE_PROMPT)
```

---

## 14. Module 2C — NLP Style DNA Analysis (Hybrid)

**Đây là khâu bạn hỏi. Bản v2 nhét tất cả vào LLM → tốn tiền, không nhất quán. Bản v3 chia 3 layer rõ ràng.**

### 14.1 Ba loại xử lý (bắt buộc phân biệt)

Xem Appendix D cho matrix đầy đủ. Tóm tắt:

| Task | Deterministic (Python) | Local ML (in Worker) | LLM |
|------|:---------------------:|:-------------------:|:---:|
| Word count, WPM | ✅ | | |
| Sentence length distribution | ✅ (`underthesea.sent_tokenize`) | | |
| Readability score | ✅ (`textstat`) | | |
| Sentiment (per sentence) | | ✅ (VADER cho EN, PhoBERT-sentiment cho VN) | |
| Emotion classification (7 emotions) | | ✅ (`j-hartmann/emotion-english-distilroberta-base`, hoặc VN: PhoBERT-emotion) | |
| N-gram signature phrases (top TF-IDF) | ✅ | | |
| Hook extraction (first 30s) | | | ✅ |
| Hook categorization | | | ✅ (constrained to fixed taxonomy) |
| Persona identification | | | ✅ |
| Structural formula (K-step) | ✅ (segment by cue words) + ✅ LLM label | | ✅ |
| Analogy detection | | | ✅ |
| Mimic Rules (11 rules) | | | ✅ (constrained output) |

### 14.2 Style DNA v3 schema (chốt)

```typescript
type StyleDNA_v3 = {
  // === Layer 1: Deterministic (từ Python) ===
  writing_metrics: {
    wpm: number;                            // 238 for Chú Béo
    sentence_length: {
      avg: number;
      p25: number; p50: number; p75: number; p95: number;
      distribution_curve: number[];         // histogram
    };
    readability: {
      flesch_reading_ease: number;
      gunning_fog: number;
      avg_syllables_per_word: number;
    };
    signature_phrases: Array<{
      phrase: string;
      frequency: number;
      tf_idf_score: number;
      example_context: string;
    }>;
  };
  
  // === Layer 2: Local ML (từ HF models) ===
  emotional_signature: {
    // 7 basic emotions from RoBERTa
    empathy_pct: number;    // = compassion + sadness
    curiosity_pct: number;  // = surprise + interest
    authority_pct: number;
    urgency_pct: number;
    mystery_pct: number;
    joy_pct: number;
    fear_pct: number;
    // Emotion curve (over time)
    curve: Array<{position_pct: number, dominant_emotion: string, intensity: number}>;
  };
  
  // === Layer 3: LLM outputs (constrained JSON) ===
  persona: {
    label: string;                          // "Grounded Empathetic Financial Mentor"
    description: string;                    // 2-3 sentences
    tone_archetype: "trusted_older_sibling" | "professor" | "hype_man" | "friend" | ...;
  };
  
  hook_analysis: {
    density_seconds: [number, number];      // [45, 90]
    types: Array<{
      name: string;                         // "Experiential Mirror Hook"
      description: string;
      count: number;
      examples: string[];                   // 2-3 real quotes
    }>;
  };
  
  structural_formula: {
    step_count: number;                     // 9 for Chú Béo, but LEARNED not fixed
    steps: Array<{
      order: number;
      name: string;                         // "Opening Question"
      description: string;
      typical_duration_pct: number;         // % of total video
      cue_phrases: string[];                // patterns that mark this section
    }>;
  };
  
  viral_topics_formula: {
    templates: Array<{
      template: string;                     // "Vì Sao [ISSUE]?"
      placeholders: Record<string, string[]>; // {ISSUE: ["Người Việt Nghèo", ...]}
      count: number;
      viral_rate: number;
    }>;
  };
  
  mimic_rules: Array<{
    id: number;
    rule_name_vi: string;                   // "MỞ ĐẦU BẰNG CHIẾC GƯƠNG CẢM XÚC"
    rule_name_en: string;
    description: string;
    example: string;
    do: string[];
    dont: string[];
  }>;  // 8-15 rules, learned per channel
};
```

### 14.3 RAG Chunking Strategy (chốt)

**Chunking algorithm:**
```python
def chunk_transcript(transcript_with_timestamps: list) -> list[Chunk]:
    """
    Semantic chunking with overlap.
    Each chunk: 3-7 sentences, ~50-150 words.
    Overlap: last 1 sentence of chunk N = first sentence of chunk N+1.
    Section labeling via cue phrases.
    """
    sentences = split_by_underthesea(transcript_with_timestamps)  # VN-aware
    chunks = []
    current = []
    for sent in sentences:
        current.append(sent)
        if len(current) >= 3 and (
            len(current) >= 7 or 
            is_section_boundary(sent, current) or
            sum(len(s.words) for s in current) >= 100
        ):
            chunks.append(Chunk(
                sentences=current,
                section=classify_section(current),   # hook | body | analogy | cta | transition
                start_ts=current[0].start_ts,
                end_ts=current[-1].end_ts,
            ))
            current = [current[-1]]  # 1-sentence overlap
    return chunks
```

**Retrieval strategy:**
```python
def retrieve_for_script_gen(topic: str, target_section: str, assistant_id: str) -> list[Chunk]:
    """
    Multi-stage retrieval:
    1. Filter by section (e.g. only 'hook' chunks when writing hook)
    2. Vector search top-20 with cosine similarity
    3. MMR rerank to top-8 (diversify)
    4. Return
    """
    topic_emb = embed(topic)  # use multilingual embed if VN
    candidates = supabase.rpc('match_dna_chunks', {
        'query_embedding': topic_emb,
        'assistant_id': assistant_id,
        'section_filter': target_section,
        'match_threshold': 0.65,  # not 0.7 — VN embeddings are lower
        'match_count': 20
    })
    return mmr_rerank(candidates, k=8, lambda_param=0.5)
```

### 14.4 Anti-AI-Slop enforcement (3-layer)

1. **In prompt:** blacklist + rule text.
2. **Regex post-check:** scan output for slop patterns → if found, retry with `[!] Detected slop phrase: X. Rewrite avoiding it.`
3. **LLM validator (Phase 2):** dedicated pass that scores output 0-100 for "AI-ness" → reject if score > 60.

Blacklist tiếng Việt (bắt buộc bổ sung, xem Appendix F):
```
"không hề đơn giản", "điều thú vị là", "bạn có biết rằng",
"trong thế giới hiện đại", "hãy tưởng tượng", "một cách đáng kinh ngạc",
"đây chính là", "đó chính là lý do", "hãy cùng nhau khám phá"
```

---

## 15. Module 2D — Structural & Hook Decoding

Chi tiết ở Section 14 (là 1 phần của DNA). Được tách section riêng vì đây là feature bán được (users hỏi mua tính năng này nhất).

Output cho user thấy:
- Bảng 9-step formula (như Chú Béo case)
- Danh sách 3-5 hook types + ví dụ trích dẫn
- Hook density heatmap

---

## 16. Module 2E — Content Gap & Idea Generation

**Đây là Output #12, #13. Bản v2 chỉ nói vắn tắt "sinh ý tưởng". Bản v3 định nghĩa gap analysis cụ thể.**

### 16.1 Gap Analysis algorithm

```
Step 1: Embed all channel titles (last 200 videos) → cluster with HDBSCAN
        → identify N topic clusters that channel HAS covered

Step 2: From Module 1 Google Trends → get top-50 rising queries + related_queries
        (in same niche)
        → Embed → cluster

Step 3: For each trending topic cluster NOT in channel's covered clusters:
        → mark as "gap opportunity"

Step 4: For each gap:
        Fill into channel's viral_topics_formula templates
        e.g. gap = "AI investing", template = "Vì Sao [ISSUE]?"
        → "Vì Sao AI Sẽ Không Thay Thế Nhà Đầu Tư Việt?"

Step 5: LLM rank & polish (UNTAPPED_OPPS_PROMPT)
        → return top 6-10 ideas with:
          - suggested_title
          - hook_snippet (mở đầu 2 câu)
          - target_duration
          - similar_video_reference (channel đối thủ đã làm gì gần nhất)
```

---

## 17. Module 3 — Script Generation + Scene Breakdown

Giữ nguyên từ v2 (Phase 2.2 + Phase 2.3), có 3 bổ sung:

- **Bổ sung 1:** Script generation dùng RAG với 8 chunks (đã chọn theo section), plug vào SCRIPT_GEN_PROMPT_V3 (Appendix E).
- **Bổ sung 2:** Post-generation validator (regex + optional LLM) → auto-retry nếu detect slop.
- **Bổ sung 3:** Scene breakdown dùng WPM đã đo được (không phải hardcode 150) để tính `estimated_duration`.

---

# PART III — APPENDICES

## Appendix A — Formulas & Thresholds Sheet

**Đây là appendix quan trọng nhất. Không có nó, AI Coding sẽ đoán số → output không so sánh được.**

### A1 — Niche Viability
```
is_viable_niche(keyword) = 
    total_views_30d >= 5_000_000                    # tổng view 30 ngày
    AND google_trends_avg_interest_3m >= 30         # not dead niche
    AND unique_channels_count >= 20                 # có cạnh tranh nhưng chưa monopoly
```

### A2 — Viral Video Definition (per channel)
```
outlier_strength(v) = (v.views - median_channel_views) / MAD(channel_views)
    where MAD = 1.4826 * median(|x_i - median(x)|)

is_viral(v) = 
    outlier_strength(v) >= 2.5
    AND (v.views / v.channel.subscribers) >= 0.3
    AND v.age_days >= 14                            # đã ổn định
    AND v.age_days <= 730                           # <= 2 năm
```

### A3 — Viral Video (across niche)
```
is_viral_in_niche(v, niche_median) = 
    v.views >= 3 * niche_median_views
    AND v.age_days <= 30
```

### A4 — Optimal Duration
```
optimal_duration_range(videos):
    viral = [v for v in videos if is_viral(v)]
    return (percentile([v.duration for v in viral], 25),
            percentile([v.duration for v in viral], 75))
    # e.g. (18:04, 20:28) for Chú Béo
```

### A5 — Consistency Score
```
consistency_score(videos):
    gaps = [videos[i].publishedAt - videos[i+1].publishedAt for i in range(len-1)]
    cv = stdev(gaps) / mean(gaps)                   # coefficient of variation
    return round(100 * max(0, 1 - cv))              # 0-100, higher = more consistent
    # Chú Béo = 65/100
```

### A6 — Optimal Tag Count
```
optimal_tag_count(videos):
    viral = [v for v in videos if is_viral(v)]
    # find mode of tag counts among viral
    counts = [len(v.tags) for v in viral]
    return statistics.mode(counts)                  # e.g. 6 for Chú Béo
```

### A7 — Tag Co-occurrence (top pairs)
```
def top_cooccurring_pairs(videos, top_n=10):
    from itertools import combinations
    pair_count = Counter()
    for v in videos:
        for a, b in combinations(sorted(set(v.tags)), 2):
            pair_count[(a, b)] += 1
    total = len(videos)
    return [
        {"pair": pair, "count": count, "pct": count/total}
        for pair, count in pair_count.most_common(top_n)
    ]
```

### A8 — Signature Phrase Extraction (n-gram TF-IDF)
```
def extract_signature_phrases(transcripts, top_k=20):
    from sklearn.feature_extraction.text import TfidfVectorizer
    # Compare channel's transcripts vs baseline corpus (VN news, general YT)
    vectorizer = TfidfVectorizer(
        ngram_range=(3, 8),                         # 3-8 gram (phrases)
        min_df=2,                                   # appears in ≥2 videos
        max_df=0.9,                                 # not overly common
        tokenizer=underthesea_tokenizer
    )
    channel_matrix = vectorizer.fit_transform(transcripts)
    baseline_matrix = vectorizer.transform(baseline_corpus)
    # Score = mean(channel_tfidf) - mean(baseline_tfidf)
    # Return top-K by score
```

### A9 — Hook Density
```
def hook_density(transcript_with_timestamps, hooks):
    """
    hooks: list of sentences pre-identified as hooks by LLM
    Returns: (min_gap, max_gap) between consecutive hooks in seconds
    """
    hook_times = [h.timestamp for h in hooks]
    gaps = [hook_times[i+1] - hook_times[i] for i in range(len(hook_times)-1)]
    return (percentile(gaps, 10), percentile(gaps, 90))
    # Chú Béo: (45, 90)
```

### A10 — Emotional Curve
```
def emotion_curve(transcript, model='j-hartmann/emotion-english-distilroberta-base'):
    """
    Split transcript into 10 equal segments (by word count).
    Run emotion classifier on each segment.
    Return time-series.
    """
    segments = split_into_n_segments(transcript, n=10)
    return [
        {"segment_idx": i,
         "position_pct": i * 10,
         "emotion_dist": model.predict_proba(seg),
         "dominant": max(dist, key=dist.get)}
        for i, seg in enumerate(segments)
    ]
```

### A11 — Structural Boundary Detection
```
def detect_structural_boundaries(transcript_sentences):
    """
    Detect topic shifts using sentence embeddings.
    Boundary = local minimum of cos_sim between consecutive sentence windows.
    """
    embeddings = [embed(s) for s in transcript_sentences]
    # window size = 3 sentences
    similarities = [
        cos_sim(mean(embeddings[max(0,i-3):i]), mean(embeddings[i:i+3]))
        for i in range(3, len(embeddings)-3)
    ]
    boundaries = find_local_minima(similarities, prominence=0.15)
    return boundaries  # list of sentence indices
```

### A12 — Success Formula Detection
```
def find_success_formulas(videos):
    """
    Find combinations of features (duration_bucket, tag_count_bucket, has_keyword_X)
    that correlate with viral status.
    Use chi-square test for significance.
    """
    features = extract_features(videos)  # dict of binary features per video
    results = []
    for feat_combo in combinations(features.keys(), 2):
        contingency = build_contingency(feat_combo, viral_labels)
        chi2, p_value = chi2_contingency(contingency)
        if p_value < 0.05:
            results.append({
                "formula": feat_combo,
                "viral_rate": ...,
                "p_value": p_value
            })
    return sorted(results, key=lambda x: x['viral_rate'], reverse=True)
```

### A13 — WPM Calculation
```
def wpm(transcript_text, video_duration_sec):
    words = len(underthesea_tokenize(transcript_text))  # for VN
    minutes = video_duration_sec / 60
    return round(words / minutes)
    # Chú Béo = 238
```

### A14 — Gap Score (Untapped Opportunity)
```
def gap_score(candidate_topic, channel_topics, trending_topics):
    emb_cand = embed(candidate_topic)
    channel_dist = 1 - max([cos_sim(emb_cand, ct) for ct in channel_topics])
        # high = far from channel's existing content
    trending_dist = min([cos_sim(emb_cand, tt) for tt in trending_topics])
        # high = close to something trending
    return 0.5 * channel_dist + 0.5 * trending_dist
```

### A15 — Slop Score (Anti-AI detector)
```
def slop_score(generated_text, blacklist):
    hits = sum(1 for phrase in blacklist if phrase.lower() in generated_text.lower())
    hits += count_generic_openers(generated_text)      # "In today's world…"
    hits += count_em_dashes(generated_text)            # em-dash overuse
    return min(100, hits * 15)                          # 0-100
    # Threshold: > 40 = reject
```

---

## Appendix B — YouTube Quota Budget & Key Rotation

### B1 — Quota cost table (units per operation)
| Operation | Units | Note |
|-----------|-------|------|
| `search.list` | 100 | 50 results max |
| `videos.list` (with statistics) | 1 | up to 50 IDs |
| `channels.list` | 1 | up to 50 IDs |
| `playlistItems.list` | 1 | up to 50 items |
| `commentThreads.list` | 1 | not used in v3 |

### B2 — Feature cost estimate
| Feature | Quota | Note |
|---------|-------|------|
| Module 1 (niche validate) | ~102 | 1 search + 1 videos + 1 channels |
| Deep collection (200 videos) | ~10 | 1 channels + 4 playlistItems + 4 videos + 1 for handle |
| Re-analyze | ~5 | Only fetch new videos since last analysis |

### B3 — Daily budget planning
- 1 API key = 10,000 units/day
- Free tier: 5 keys × 10,000 = 50,000 units/day
- Est. capacity: ~450 niche validations OR ~4,900 channel deep analyses / day

### B4 — Circuit breaker
```python
if quota_used_today / quota_total >= 0.8:
    log_warning("Quota 80% used, switching to degraded mode")
    disable_features(['module1_search'])
    enable_features(['cached_only'])
```

---

## Appendix C — External API Fallback Matrix

| Purpose | Tier 1 (free/preferred) | Tier 2 (paid backup) | Tier 3 (last resort) |
|---------|-------------------------|----------------------|----------------------|
| Transcript | `youtube-transcript-api` + residential proxy | Supadata / youtube-transcript.io ($0.001/min) | `yt-dlp` audio → Whisper ($0.006/min) |
| Video footage | Pexels video | Pixabay video | Image (Unsplash/Pexels) → Ken Burns effect |
| Image footage | Unsplash | Pexels | AI-gen (nano-banana-2, $0.02/img) |
| Trends | `pytrends` (unofficial) | SerpAPI Google Trends ($75/mo) | Skip + warn user |
| LLM | OpenAI GPT-4o | Gemini 1.5 Pro | Anthropic Claude 3.5 Sonnet |
| Embeddings | `text-embedding-3-small` (EN + VN partial) | Cohere `embed-multilingual-v3` | Local `intfloat/multilingual-e5-large` |
| Emotion classifier | HF `j-hartmann/emotion-...` | HF `PhoBERT-emotion-vn` | LLM (last resort, expensive) |
| Sentence tokenizer VN | `underthesea` | `pyvi` | spaCy multilingual |

**Retry policy:**
- Transient errors (5xx, timeout, rate limit): exponential backoff (base=2s, max=60s, retries=5)
- Auth errors (401, 403 quota): immediate switch to next tier
- Not found (404): fallback to next tier

---

## Appendix D — Deterministic vs LLM vs Local-ML Task Matrix

**Nguyên tắc vàng:** *If a formula exists, don't use LLM.*

| # | Sub-task | Python (pure) | Local ML (HF) | LLM |
|---|----------|:-------------:|:-------------:|:---:|
| 1 | Extract video metadata (title, tags, duration) | ✅ | | |
| 2 | Compute upload frequency | ✅ | | |
| 3 | Compute duration percentiles | ✅ | | |
| 4 | Tag frequency + co-occurrence | ✅ | | |
| 5 | Outlier detection (viral videos) | ✅ | | |
| 6 | Signature phrase extraction (TF-IDF n-gram) | ✅ | | |
| 7 | WPM calculation | ✅ | | |
| 8 | Sentence length distribution | ✅ | | |
| 9 | Readability (Flesch, Gunning Fog) | ✅ (`textstat`) | | |
| 10 | Detect language (VN vs EN) | ✅ (`langdetect`) | | |
| 11 | Tokenize VN | ✅ (`underthesea`) | | |
| 12 | Sentiment per sentence | | ✅ VADER/PhoBERT | |
| 13 | Emotion classification (7-class) | | ✅ RoBERTa | |
| 14 | Emotional curve over transcript | | ✅ | |
| 15 | Structural boundary detection (embed similarity) | ✅ + embedding | | |
| 16 | Hook extraction & categorization | | | ✅ (constrained) |
| 17 | Persona identification | | | ✅ |
| 18 | Structural formula labeling | | | ✅ |
| 19 | Analogy detection | | | ✅ |
| 20 | Signature phrase context labeling | | | ✅ (small task) |
| 21 | Mimic rules generation | | | ✅ |
| 22 | Viral topic formula templates | ✅ regex cluster | | ✅ label |
| 23 | Untapped opportunity ideas | ✅ gap score | | ✅ polish |
| 24 | Hidden insight narration | ✅ stats | | ✅ narrate (last step) |
| 25 | Script generation (with RAG) | | | ✅ |
| 26 | Scene breakdown | | | ✅ (JSON constrained) |
| 27 | Anti-slop regex check | ✅ | | |
| 28 | Anti-slop semantic check (Phase 2) | | | ✅ |
| 29 | Thumbnail analysis | | | ✅ Vision |
| 30 | Search keyword translation (VN→EN for Pexels) | | | ✅ (or Google Translate API) |
| 31 | Duration estimation from text | ✅ (word_count / WPM) | | |
| 32 | Chunking transcript (RAG index) | ✅ | | |
| 33 | Embedding for RAG | | ✅ (embed API) | |
| 34 | MMR reranking | ✅ | | |
| 35 | Consistency score | ✅ | | |
| 36 | Google Trends fetch | ✅ (`pytrends`) | | |
| 37 | Trends signal interpretation | | | ✅ (optional) |
| 38 | Video filter (Shorts, live, restricted) | ✅ | | |
| 39 | Channel dedup | ✅ | | |
| 40 | Format duration/date for UI | ✅ | | |

---

## Appendix E — Prompt Templates + Test Suite

### E1 — Master rules (áp cho MỌI prompt)
```
[SYSTEM RULES]
- Output MUST be valid JSON matching provided schema.
- Do NOT include commentary before/after JSON.
- Use Vietnamese for all human-facing text unless field name says "_en".
- If unsure, use null. Do NOT hallucinate.
```

### E2 — STYLE_DNA_PROMPT_V3 (structured)
```
[TASK] Extract Style DNA from these {N} viral video transcripts of channel {channel_name}.

[TRANSCRIPTS]
{% for t in transcripts %}
--- Video: {t.title} (views: {t.views}, duration: {t.duration}) ---
{t.text}
{% endfor %}

[REQUIRED OUTPUT: JSON matching StyleDNA_v3 schema]
{
  "persona": {"label": ..., "description": ..., "tone_archetype": ...},
  "hook_analysis": {...},
  "structural_formula": {"step_count": N, "steps": [...]},
  "viral_topics_formula": {"templates": [...]},
  "mimic_rules": [8-15 rules],
  ...
}

[CONSTRAINTS]
- Persona label = 3-5 words, English
- Structural steps = 5-12, labeled with cue phrases from actual transcripts
- Mimic rules must reference specific evidence from transcripts (quote real phrases)
- NO generic descriptions like "engaging" or "informative"
```

### E3 — SCRIPT_GEN_PROMPT_V3 (with RAG)
```
[TASK] Write a YouTube video script in the style of {persona} on topic: "{topic}"

[STYLE RULES — MUST FOLLOW]
{mimic_rules_formatted}

[REFERENCE PASSAGES from this creator — mimic vocabulary, sentence rhythm, cadence]
{% for chunk in rag_chunks_8 %}
[Reference #{loop.index} | section={chunk.section}]:
{chunk.text}
{% endfor %}

[STRUCTURAL FORMULA — follow this order]
{structural_formula_9_steps}

[FORBIDDEN — do NOT use these phrases]
{blacklist_slop_vn}

[OUTPUT RULES]
- Vietnamese only
- Target duration: {target_min} minutes at {wpm} WPM = ~{target_words} words
- Structure: Hook (0:00-0:30) → ... → CTA (final 30s)
- Do NOT include any visual/scene directions ("*Cut to*", "[Image of...]", stage directions)
- Do NOT number sections. Just write flowing narration.
- Use analogies rooted in Vietnamese daily life (per Mimic Rule #4)
```

### E4 — SCENE_BREAKDOWN_PROMPT_V3
```
[TASK] Break the script below into scenes for B-roll footage sourcing.

[SCRIPT]
{script_text}

[OUTPUT: JSON array of scenes]
[
  {
    "scene_id": 1,
    "text": "<Vietnamese narration for this scene>",
    "estimated_duration_sec": <computed as word_count / {wpm} * 60>,
    "visual_context": "<English description of what should be shown>",
    "search_keyword_en": "<English keyword for Pexels API>",
    "asset_type": "video" | "image",
    "mood": "calm" | "energetic" | "serious" | "playful"
  },
  ...
]

[RULES]
- One scene = 3-8 seconds of narration (about 15-30 Vietnamese words)
- Do NOT split a sentence across scenes
- search_keyword_en must be 2-5 English words that Pexels/Pixabay understand
- If a scene shows an abstract concept, prefer asset_type=image
```

### E5 — HIDDEN_INSIGHTS_NARRATE_PROMPT
```
[TASK] Convert these statistical findings into 3-5 natural Vietnamese insights.

[FINDINGS]
{findings_json}

[RULES]
- Only mention findings with p_value < 0.05 (already filtered)
- Format each insight: 1 headline (max 12 words) + 1-2 sentence explanation
- Do NOT add speculation beyond the data
- Use Vietnamese only
```

### E6 — MIMIC_TONE_PROMPT
```
[TASK] Given the persona, emotional signature, and 8 transcript excerpts, generate 8-15 concrete mimicry rules.

Each rule must:
1. Be actionable (can be checked by another AI)
2. Reference specific evidence (quote from transcript)
3. Include DO and DON'T examples
4. Follow this Vietnamese-heavy structure like:
   "MỞ ĐẦU BẰNG CHIẾC GƯƠNG CẢM XÚC: [description] Example: '...' DON'T: '...'"

[OUTPUT: JSON array]
[{"id": 1, "rule_name_vi": "...", "description": "...", "example": "...", "do": [...], "dont": [...]}]
```

### E7 — THUMBNAIL_ANALYSIS_PROMPT (Vision)
```
[TASK] Analyze these {N} thumbnail images of viral videos.

[OUTPUT JSON]
{
  "dominant_colors": ["#FF5500", "#000000"],
  "color_palette_mood": "high-contrast bold" | "muted professional" | ...,
  "text_usage": {
    "avg_text_words": 4,
    "text_position": "left" | "center" | "right",
    "font_style": "sans-serif bold" | ...
  },
  "face_expressions": ["shocked", "pointing", "thinking"],
  "composition": "single subject" | "split screen" | "before-after",
  "recurring_elements": ["yellow arrow", "red circle", "money stack"]
}
```

### E8 — Test Suite (Regression)
Mỗi prompt cần 3 test case (VN + EN):
```
tests/
  test_style_dna_v3.py
    def test_chu_beo_style_dna():
        result = run_prompt(STYLE_DNA_PROMPT_V3, chu_beo_5_transcripts)
        assert result['persona']['tone_archetype'] == 'trusted_older_sibling'
        assert 5 <= result['structural_formula']['step_count'] <= 12
        assert len(result['mimic_rules']) >= 8
        assert any('ẩn dụ' in r['description'] for r in result['mimic_rules'])
```

---

## Appendix F — Vietnamese-specific Config

### F1 — Slop blacklist (VN)
```python
SLOP_VN = [
    "không hề đơn giản", "điều thú vị là", "bạn có biết rằng",
    "trong thế giới hiện đại ngày nay", "hãy tưởng tượng",
    "một cách đáng kinh ngạc", "đây chính là", "đó chính là lý do",
    "hãy cùng nhau khám phá", "trong bài viết này chúng ta sẽ",
    "vô cùng quan trọng", "không thể phủ nhận rằng",
    "một điều chắc chắn rằng", "khi nói đến", "đối với nhiều người"
]
```

### F2 — Tokenizer & POS
```python
from underthesea import word_tokenize, sent_tokenize, pos_tag
# For chunking, use sent_tokenize
# For n-gram, use word_tokenize with format="text"
```

### F3 — Timezone default
```python
DEFAULT_TZ = "Asia/Ho_Chi_Minh"  # UTC+7
# When showing "kênh này đăng vào 7h tối" — convert publishedAt (UTC) to VN TZ
# Caveat: This is CREATOR's upload time, not audience prime time.
# For audience prime time → require YouTube Analytics API (channel-owner-only).
```

### F4 — Emotion model for VN
```
Primary: wonrax/phobert-base-vietnamese-emotion (7-class)
Fallback: translate VN → EN → run j-hartmann/emotion-english-distilroberta-base
```

### F5 — Cultural context injection (for mimic rules)
Include in `STYLE_DNA_PROMPT_V3` a note:
```
[CONTEXT] The creator is Vietnamese, targeting Vietnamese audience.
Prefer analogies grounded in Vietnamese daily life (đẩy xe máy, kiến tha lâu, ...).
Include Vietnamese proverbs (tục ngữ) where they appear in the source.
```

---

## Appendix G — 13 Outputs Dependency DAG

```
                    ┌─────────────────────────────┐
                    │ Raw video list (200 videos) │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌────────────────────────┐   ┌──────────────────────────┐
       │ 1. Metadata Report     │   │ Fetch transcripts for    │
       │ 2. Tags Report         │   │ top-5 viral videos       │
       │ 3. Performance Report  │   │ + thumbnails             │
       └────────┬───────────────┘   └───────┬──────────────────┘
                │                           │
                ▼                           │
       ┌─────────────────────┐              │
       │ 4. Hidden Insights  │              │
       └─────────────────────┘              │
                                            │
                    ┌───────────────────────┼────────────────────┐
                    ▼                       ▼                    ▼
       ┌────────────────────┐   ┌──────────────────┐   ┌────────────────────┐
       │ 5. Persona         │   │ 6. Pacing Profile│   │ Thumbnail Analysis │
       │ 8. Hook Analysis   │   │ 7. Emotion Sig.  │   │ (Vision LLM)       │
       │ 9. Structural Form.│   │ 10. Sig. Phrases │   └────────────────────┘
       └────────────┬───────┘   └────────┬─────────┘
                    │                    │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ 11. Mimic Rules    │
                    └─────────┬──────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ 12. Viral Topics │  │ RAG index build  │  │ Content Calendar   │
│ Formula          │  │ (dna_chunks)     │  │ (from #1)          │
└────────┬─────────┘  └──────────────────┘  └────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 13. Untapped Opportunities │  ← also needs Google Trends
└────────────────────────────┘
```

**Pipeline execution order:**
1. Parallel batch 1: `[1, 2, 3]` + `fetch_transcripts` + `fetch_thumbnails`
2. Sequential: `[4]` after `[1,2,3]`
3. Parallel batch 2: `[5, 6, 7, 8, 9, 10]` after transcripts ready
4. Sequential: `[11]` after `[5-10]`
5. Parallel batch 3: `[12, RAG build]` after `[11]`
6. Final: `[13]` after `[12]` + Google Trends

---

## Appendix H — Cost Model per Action (Credit Pricing)

**Assumption:** 1 credit = $0.01. Target margin: 60-70%.

### H1 — Cost breakdown per action

| Action | External cost | Suggested credits | Margin |
|--------|--------------|-------------------|--------|
| Niche validate (Module 1) | $0.02 (LLM $0.015 + YT $0 + Trends $0.005) | 5 credits ($0.05) | 60% |
| Deep channel analysis (13 outputs, no transcript) | $0.35 (LLM $0.30 + YT $0 + Embed $0.05) | 100 credits ($1.00) | 65% |
| Transcript fetch (per video, ~15 min) | $0.09 (Whisper worst-case) | 10 credits ($0.10) | 10% (thin margin, needs tier 1 success rate 80%+) |
| Script generation (10 min video, ~2500 words) | $0.055 (GPT-4o) | 20 credits ($0.20) | 72% |
| Scene breakdown + Pexels footage (40 scenes) | $0.02 (LLM) + Pexels free | 10 credits ($0.10) | 80% |
| Thumbnail analysis | $0.02 (Vision LLM) | 5 credits ($0.05) | 60% |

### H2 — Full "clone a channel + write 1 script" journey
```
Niche validate:        5 credits
Deep analysis:       100 credits
5× transcript:        50 credits (5 × 10)
Script gen:           20 credits
Scene breakdown:      10 credits
───────────────────────────────
TOTAL:               185 credits ≈ $1.85 to user
Our cost:            ~$0.60
Margin:              ~68%
```

### H3 — BYOK (Bring Your Own Key) discount
Nếu user cung cấp OpenAI key → credits × 0.3 (chỉ trả cho YT quota + infra).

### H4 — Abuse prevention hard caps
```
FREE tier:
  - 3 concurrent jobs max
  - 500 credits/day hard cap
  - 5 assistants max
  - 20 script/month max

PRO tier:
  - 10 concurrent jobs
  - 5,000 credits/day
  - Unlimited assistants
  - Unlimited scripts
```

---

## Appendix I — Legal / ToS Compliance

### I1 — YouTube Terms of Service
- Only use YouTube Data API v3 for structured data.
- **DO NOT** scrape youtube.com HTML.
- yt-dlp usage: only for **user's own owned channels** OR clearly note it's user's responsibility (add checkbox in UI).
- Cache expiration: comply with YouTube API TOS (do not permanently store data).

### I2 — Transcript
- `youtube-transcript-api` reads publicly available captions — legal.
- Whisper transcription: fair use for analysis, but do not redistribute raw transcripts as content.

### I3 — Attribution
- Pexels: attribution not required but appreciated. Add small "Powered by Pexels" in UI.
- Unsplash: attribution required (photographer name + link) — must display in Scene Editor.
- Pixabay: no attribution required.

### I4 — Copyright of generated scripts
- User owns generated scripts (per Terms of Service).
- But we disclaim: generated script may inadvertently overlap with source content — user's responsibility to check.

### I5 — GDPR / user data
- Delete all user data + assistants + transcripts within 30 days of account deletion.
- Include data export endpoint (JSON dump of user's assistants + projects).

---

## Appendix J — Sprint Roadmap

### Phase 1 (8 weeks, MVP)

**Sprint 1 (2 weeks) — Foundation**
- Monorepo setup + CI/CD
- Supabase schema + RLS
- Module 0-Lite (auth, credit hold/commit/release)
- FastAPI skeleton + Celery worker skeleton
- Realtime subscription setup

**Sprint 2 (2 weeks) — YouTube Collection Engine**
- Module 2A: YouTube API client with quota rotation
- Redis cache with stampede prevention
- Video filter (Shorts, live, restricted)
- Transcript 3-tier fallback
- `quota_ledger` + monitoring

**Sprint 3 (2 weeks) — Deterministic Analysis**
- Module 2B: Metadata + Tags + Performance report (Outputs 1-4)
- Appendix A formulas (all 15)
- `channel_deep_analysis` table populate
- Basic UI to view results

**Sprint 4 (2 weeks) — NLP DNA + Script Gen (basic)**
- Module 2C: Style DNA v3 (Outputs 5-11) — LLM path first, Local ML in Phase 2
- Module 3: Script generation with RAG
- Scene breakdown + Pexels fetch
- End-to-end demo: URL → Analysis → Script → Scenes

### Phase 2 (6 weeks, Polish)

**Sprint 5 — Local ML pipeline**
- Add PhoBERT emotion model in worker
- Emotional curve visualization
- Anti-slop LLM validator
- Signature phrase extraction (TF-IDF)

**Sprint 6 — Content Gap + Trends**
- Module 2E: Untapped Opportunities (Output 13)
- pytrends integration
- Viral topics formula clustering (Output 12)

**Sprint 7 — Module 0 Full**
- OAuth Google/Facebook
- Stripe integration
- Multi-tier plans
- Team support
- Admin dashboard

**Sprint 8 — Vision + Polish**
- Thumbnail analysis (Vision LLM)
- Content calendar UI
- Export PDF report
- Public beta launch

---

## KẾT LUẬN (SUMMARY OF CHANGES v2 → v3)

| # | Thay đổi | Impact |
|---|----------|--------|
| 1 | Bổ sung 6 bảng DB mới (jobs, credit_tx, api_usage_logs, quota_ledger, dna_chunks, channel_deep_analysis) | HIGH |
| 2 | Định nghĩa rõ **13 outputs** với DAG dependency | HIGH |
| 3 | Tách 3 pipeline: **Deterministic / Local ML / LLM** với Appendix D matrix | HIGH |
| 4 | 15 công thức toán học cụ thể (Appendix A) — thay thế mọi "magic number" | CRITICAL |
| 5 | YouTube quota rotation + cache stampede prevention (Appendix B) | HIGH |
| 6 | External API 3-tier fallback matrix (Appendix C) | HIGH |
| 7 | Bổ sung **Google Trends** vào Module 1 (loại bỏ SocialBlade) | MEDIUM |
| 8 | RAG chunking algorithm cụ thể + MMR rerank | MEDIUM |
| 9 | Anti-AI-Slop 3-layer enforcement (in-prompt + regex + LLM validator) + slop VN blacklist | MEDIUM |
| 10 | Local ML pipeline (PhoBERT-emotion, VADER, textstat) thay LLM cho các task đo lường | HIGH cost saving |
| 11 | Prompt Test Suite (regression testing) | MEDIUM |
| 12 | Cost model per action + BYOK discount + abuse hard caps | HIGH |
| 13 | Legal/ToS section (yt-dlp risk, Unsplash attribution) | MEDIUM |
| 14 | Sprint roadmap 14 tuần (Phase 1: 8w, Phase 2: 6w) | HIGH |

**Với v3 này, AI Coding có thể sinh code chạy được ~95% mà không phải đoán thêm.**
