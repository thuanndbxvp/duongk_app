# STACK REFERENCE — YouTube AI SaaS

> **Đọc file này trước khi làm bất kỳ task nào.** Đây là stack đã chốt, KHÔNG được giả định khác.

---

## Kiến trúc tổng thể

```
User Browser
    │ HTTPS
    ▼
[Cloudflare DNS + WAF + CDN]
    │
    ▼
[CPU VPS — Ubuntu 24.04]              ← SaaS core
├── Caddy (reverse proxy, auto SSL)
├── Next.js (App Router, SSR)         ← Frontend
├── FastAPI (Python 3.12)             ← Backend REST API
├── Celery worker (nhẹ, orchestration)
└── Redis (queue broker + cache)
    │
    ├──► [Supabase managed]           ← Auth + Postgres + RLS + Realtime
    │
    ├──► [GPU VPS]                    ← Heavy compute
    │    ├── FFmpeg render (NVENC)
    │    ├── Whisper ASR
    │    ├── Local ML inference
    │    └── Optional: local LLM (Ollama/vLLM)
    │
    └──► [Cloudflare R2]              ← Object storage (egress FREE)
         ├── appdk-uploads
         ├── appdk-renders
         └── appdk-cache

```

---

## 4 thành phần chính

### 1. CPU VPS (Ubuntu 24.04)
- **Vai trò:** SaaS core, orchestration, KHÔNG chạy AI/render nặng
- **Chạy:** Next.js + FastAPI + Celery worker (light) + Redis + Caddy + OmniVoice
- **KHÔNG chạy:** LLM inference, FFmpeg render, Whisper — những cái này phải push sang GPU VPS hoặc Modal
- **Deploy:** Docker Compose, quản lý bằng `docker-compose.prod.yml`
- **Path chuẩn:** `/opt/appdk/`
- **IP:** `161.248.4.99`

### 2. GPU VPS / Serverless Modal
- **Vai trò:** Heavy compute worker & AI Inference
- **Chạy:** FFmpeg render (h264_nvenc), Whisper transcript, OmniVoice TTS & Dubbing (`modal_functions/dubbing_pipeline.py`)
- **Giao tiếp với CPU VPS:** qua Modal SDK / private network / message queue
- **KHÔNG chạy:** web/API/auth — những cái đó ở CPU VPS

### 3. Supabase managed
- **Vai trò:** Source of truth cho user/auth/credit/project
- **Chứa:**
  - Auth (email/password, JWT)
  - Postgres 15 (với RLS bật toàn bộ)
  - Extensions: `pgvector`, `pg_cron`, `uuid-ossp`
  - Realtime (subscribe DB changes cho progress bar)
- **KHÔNG self-host** — dùng managed để tránh ops burden
- **Region:** Southeast Asia (Singapore)

### 4. Cloudflare R2
- **Vai trò:** Object storage cho mọi media/output
- **Ưu điểm chính:** Egress MIỄN PHÍ
- **API:** S3-compatible (dùng `boto3`)
- **Buckets (Chính xác theo Cloudflare R2):**
  - `appdk-uploads` — user upload input & reference audio
  - `appdk-renders` — video/audio output từ render pipeline & TTS
  - `appdk-cache` — thumbnail, preview (TTL 7 ngày)

- **CDN:** custom domain `cdn.ai86.click` cho public serving

---

## Nguyên tắc bất di bất dịch

### 1. Phân tách compute theo node
- **CPU VPS** → web/API/orchestration/deterministic analytics
- **GPU VPS** → FFmpeg render, ASR, ML inference
- **NEVER** chạy Whisper/FFmpeg trên CPU VPS chính (sẽ làm lag toàn hệ thống)

### 2. Auth flow
- **BFF pattern:** Browser → Next.js Route Handler → FastAPI
- Next.js verify Supabase session cookie
- FastAPI verify Supabase JWT với `SUPABASE_JWT_SECRET` (HS256)
- **KHÔNG** cho browser gọi trực tiếp FastAPI

### 3. API Keys quản lý qua Admin Panel
- **KHÔNG thêm API keys mới vào `.env`** — trái với principle
- Mọi provider key (OpenAI, Gemini, Groq, ElevenLabs, ...) đều lưu trong bảng `api_provider_keys` (Supabase Vault encrypted)
- Worker đọc key qua `key_resolver.get_active_key(provider_name)`
- Chỉ credentials hạ tầng (Supabase URL, R2 access key, Redis URL) mới nằm trong `.env`

### 4. Service Routing quản lý qua Admin Panel
- Mỗi feature (transcript, LLM, TTS, render, ...) có bảng `service_routing_config`
- Admin quyết định primary + fallback chain qua UI `/admin/routing`
- Worker hot-reload config qua Redis pub/sub, không cần restart
- **KHÔNG hardcode** provider preference trong code

### 5. Realtime
- Dùng **Supabase Realtime** subscribe `jobs.progress`
- **KHÔNG** build WebSocket riêng
- **KHÔNG** polling `GET /jobs/:id` (chỉ dùng khi Realtime fail)

### 6. Credit system
- **Hold-Commit-Release** pattern (atomic Postgres RPC)
- Hold khi tạo job → Commit khi success → Release (refund) khi fail
- Partial commit: `partial_commit_credits(user_id, job_id, actual_cost)` cho transcript tiering

### 7. Storage
- **Media/output** → luôn dùng R2 (không lưu local trên VPS)
- **Temp files** → GPU VPS local NVMe, xóa sau job
- **DB backup** → export lên R2 hàng ngày qua cron

---

## Tech stack chi tiết

| Layer | Chốt | Version |
|---|---|---|
| Frontend | Next.js App Router + React + TailwindCSS + shadcn/ui | Next.js 15, React 19 |
| Backend REST | Python + FastAPI + Pydantic v2 | Python 3.12, FastAPI 0.115+ |
| Worker | Celery + Redis | Celery 5.4, Redis 7 |
| Database | Supabase Postgres + pgvector + pg_cron | Postgres 15 |
| Auth | Supabase Auth (email/password, JWT HS256) | — |
| Realtime | Supabase Realtime | — |
| LLM | Provider quản lý qua Admin Panel (OpenAI, Gemini, Groq, ...) | — |
| Embedding | Auto-router: `text-embedding-3-small` (EN) + Cohere multilingual (VN) | dim=1024 |
| Local NLP | `underthesea` (VN), `textstat`, PhoBERT-emotion (MIT) | — |
| Transcript | 3-tier fallback: caption → Supadata → ASR (Groq/OpenAI/Modal/local Whisper) | quản lý routing qua Admin |
| Render | FFmpeg với `h264_nvenc` (GPU VPS) | — |
| Object Storage | Cloudflare R2 (S3-compatible, egress free) | — |
| Reverse proxy | Caddy 2 (auto SSL Let's Encrypt) | — |
| Deploy | Docker Compose | — |
| Monitoring | Sentry + UptimeRobot + Better Stack | — |

---

## Cấu trúc monorepo
 
 ```
 /apps
   /web                     # Next.js 15 (BFF pattern)
   /api                     # FastAPI (REST API, không có LLM key trong env)
   /worker                  # Celery worker (đọc key từ Vault qua key_resolver)
   /omnivoice               # Voice Studio (voice.ai86.click, port 8088, catalog & UI)
   /admin                   # Admin panel (route /admin/* trong apps/web)
 /packages
   /shared-types            # Pydantic → TypeScript auto-gen
   /prompts                 # LLM prompt templates
   /formulas                # Pure Python statistics
   /nlp                     # Tokenizer, sentiment, readability
 /supabase
   /migrations              # SQL migrations (versioned)
   /policies                # RLS policies
   /seed                    # Test data + routing config seed
 /modal_functions           # Modal.com serverless GPU functions (dubbing_pipeline.py)
 /docs
   /audit
   /plans
 ```
 
 ---
 
 ## Environment variables (chỉ hạ tầng, KHÔNG có LLM keys)
 
 ```bash
 # Supabase
 SUPABASE_URL=
 SUPABASE_ANON_KEY=
 SUPABASE_SERVICE_ROLE_KEY=
 SUPABASE_JWT_SECRET=
 
 # Cloudflare R2
 R2_ACCESS_KEY_ID=
 R2_SECRET_ACCESS_KEY=
 R2_ENDPOINT=
 R2_BUCKET_UPLOADS=appdk-uploads
 R2_BUCKET_RENDERS=appdk-renders
 R2_BUCKET_CACHE=appdk-cache
 R2_PUBLIC_CDN=https://cdn.ai86.click
 
 # Redis
 REDIS_URL=redis://redis:6379/0
 
 # App
 DOMAIN=ai86.click
 NEXT_PUBLIC_APP_URL=https://ai86.click
 NEXT_PUBLIC_SUPABASE_URL=
 NEXT_PUBLIC_SUPABASE_ANON_KEY=
 
 # GPU VPS / Modal
 GPU_WORKER_URL=
 GPU_WORKER_TOKEN=
 
 # ============ KHÔNG THÊM VÀO ĐÂY ============
 # ❌ OPENAI_API_KEY
 # ❌ GEMINI_API_KEY
 # ❌ GROQ_API_KEY
 # ❌ ELEVENLABS_API_KEY
 # ❌ COHERE_API_KEY
 # Các key AI provider quản lý qua Admin Panel + Supabase Vault
 # ============================================
 ```
 
 ---
 
 ## Anti-patterns (KHÔNG làm)
 
 - ❌ Chạy FFmpeg/Whisper trên CPU VPS chính
 - ❌ Thêm API key AI provider vào `.env`
 - ❌ Hardcode `os.environ.get('OPENAI_API_KEY')` trong code
 - ❌ Build WebSocket riêng thay vì Supabase Realtime
 - ❌ Cho browser gọi trực tiếp FastAPI (phải qua BFF)
 - ❌ Self-host Supabase / Postgres (giữ managed)
 - ❌ Lưu media output trên VPS local (phải dùng R2)
 - ❌ Hardcode provider preference trong worker (phải qua `service_routing_config`)
 - ❌ Skip RLS policy khi tạo bảng mới có `user_id`
 - ❌ Polling job status (dùng Realtime)
 
 ---
 
 ## Khi AI làm task mới, checklist bắt buộc:
 
 - [ ] Task này thuộc CPU VPS hay GPU VPS?
 - [ ] Có cần API key mới không? Nếu có → thêm qua Admin Panel, KHÔNG env
 - [ ] Có cần routing feature mới không? Nếu có → thêm vào `service_routing_config`
 - [ ] Có RLS policy cho bảng mới không?
 - [ ] Realtime subscription hay polling?
 - [ ] File output đi R2 hay local disk?
 - [ ] Credit hold/commit/release đầy đủ chưa?
 
 ---
 
 ## Quy trình Triển khai (Deployment Workflow)
 
 Xem hướng dẫn thao tác chi tiết tại [RUN.md] cùng thư mục \docs\important\.
 
 ### 1. Tự động qua script (Recommended):
 ```powershell
 git add . && git commit -m "feat/fix: update" && git push
 python update.py
 ```
 
 ### 2. Thao tác thủ công qua SSH:
 ```bash
 ssh deploy@161.248.4.99
 # pass: hJ%ExH;V_#|6
 
 cd /opt/appdk
 git pull origin main
 docker compose -f docker-compose.prod.yml up -d --build
 docker compose -f docker-compose.prod.yml ps
 docker compose -f docker-compose.prod.yml logs -f --tail=50
 ```