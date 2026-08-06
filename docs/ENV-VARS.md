# Environment Variables Reference

> Liệt kê tất cả biến môi trường trong `.env`. Required = app sẽ crash nếu thiếu. Optional = fallback an toàn.

## Supabase (5 — all required)

| Biến | Mô tả | Nguồn |
|------|-------|-------|
| `SUPABASE_URL` | Project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Public anon key | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side key (bypass RLS) | Supabase Dashboard → Settings → API ⚠️ KHÔNG commit |
| `NEXT_PUBLIC_SUPABASE_URL` | Mirror cho Next.js client | Copy từ SUPABASE_URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Mirror cho Next.js client | Copy từ SUPABASE_ANON_KEY |
| `SUPABASE_JWT_SECRET` | Verify JWT | Supabase Dashboard → Settings → API → JWT Secret |

## Redis (3 — all required nếu chạy worker)

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `REDIS_URL` | Redis connection cho app | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/0` |

## Cloudflare R2 (7 — required cho TTS voice feature)

| Biến | Mô tả |
|------|-------|
| `R2_ACCESS_KEY_ID` | R2 API token |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_ENDPOINT` | Endpoint URL |
| `R2_BUCKET_UPLOADS` | Bucket cho user uploads |
| `R2_BUCKET_RENDERS` | Bucket cho rendered videos |
| `R2_BUCKET_CACHE` | Bucket cho cache |
| `R2_PUBLIC_CDN` | Public URL prefix |

Nguồn: Cloudflare Dashboard → R2 → Manage R2 API Tokens.

## Modal (2 — required cho TTS)

| Biến | Mô tả |
|------|-------|
| `MODAL_TOKEN_ID` | Modal auth token ID |
| `MODAL_TOKEN_SECRET` | Modal auth token secret |

Nguồn: https://modal.com → Settings → Tokens.

## LLM (3 — required)

| Biến | Mô tả | Nguồn |
|------|-------|-------|
| `OPENAI_API_KEY` | OpenAI GPT-4o, Whisper | https://platform.openai.com/api-keys |
| `COHERE_API_KEY` | Cohere Embed v3 | https://dashboard.cohere.com/api-keys |
| `YOUTUBE_API_KEY_1` | YouTube Data API v3 | Google Cloud Console |

## Groq (optional — preferred for ASR)

| Biến | Mô tả | Nguồn |
|------|-------|-------|
| `GROQ_API_KEY` | Groq Whisper Large v3 Turbo (FREE 2,000 req/ngày + 28,800 audio-sec/ngày) | https://console.groq.com/keys |

> **NOTE**: Từ Phase 5, tất cả API keys (kể cả Groq) được quản lý qua Admin UI `/admin/api-keys`. Env vars là fallback cho worker.

## External APIs (2 — required cho tier 2 fallback)

| Biến | Mô tả | Nguồn |
|------|-------|-------|
| `SUPADATA_API_KEY` | Tier 2 transcript ($0.001/min) | https://supadata.ai |
| `SERPAPI_KEY` | Fallback niche validation | https://serpapi.com |

## Optional / unused

| Biến | Mô tả |
|------|-------|
| `STALI_API_KEY`, `STALI_BASE_URL` | LLM provider dự phòng — **không có consumer trong code hiện tại**, giữ lại cho tương lai |
| `SENTRY_DSN` | Error tracking (optional — nếu None thì no-op) |
| `PYTHONUNBUFFERED` | `1` để log Python flush ngay |

## Admin panel (1)

| Biến | Mô tả |
|------|-------|
| `ADMIN_ALLOWED_IPS` | Comma-separated CIDR (e.g. `127.0.0.1,::1,1.2.3.4/32`) — IP whitelist cho admin endpoints |