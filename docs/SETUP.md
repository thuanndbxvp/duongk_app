# AppDK — Setup Guide (5 phút cho dev mới)

> Tài liệu này hướng dẫn setup dự án từ zero. Mục tiêu: chạy được FastAPI + Web + Worker trên localhost.

## 1. Clone & Install

```bash
git clone <repo-url>
cd appDK

# Python deps (API + Worker)
cd apps/api
pip install -r requirements.txt   # nếu chưa có, dùng pyproject.toml
cd ../worker
pip install -r requirements.txt
cd ../..

# Node deps (Web)
cd apps/web
pnpm install
cd ../..
```

## 2. Tạo `.env` từ template

```bash
cp .env.example .env
```

Sau đó mở `.env` và điền các giá trị thật:
- `SUPABASE_URL`, `SUPABASE_*_KEY`: lấy từ https://app.supabase.io → Project → Settings → API
- `OPENAI_API_KEY`: https://platform.openai.com/api-keys
- `YOUTUBE_API_KEY_1`: Google Cloud Console → YouTube Data API v3
- (Chi tiết từng biến: xem `docs/ENV-VARS.md`)

## 3. Verify env

```bash
python scripts/check-env.py
```

Output phải hiện `[OK] TÊN_BIẾN` cho tất cả required variables. Nếu có `[MISSING]`, quay lại bước 2.

## 4. Apply DB migrations

Nếu dùng local Postgres:
```bash
supabase db reset   # chạy tất cả migrations từ supabase/migrations/
```

Nếu dùng Supabase managed:
- Vào Dashboard → SQL Editor → chạy lần lượt các file `supabase/migrations/0001..0023` (theo thứ tự tên).

## 5. Start services

```bash
# Terminal 1: FastAPI
cd apps/api
uvicorn main:app --reload --port 8000

# Terminal 2: Celery worker
cd apps/worker
celery -A celery_app worker --loglevel=info

# Terminal 3: Next.js web
cd apps/web
pnpm dev
```

Mở browser: http://localhost:3000

## Troubleshooting

- **"ModuleNotFoundError: apps.api..."**: chạy từ root `appDK`, không từ `apps/api`.
- **"Invalid API key"** (Supabase): check `.env` có `SUPABASE_*` đúng chưa.
- **"Connection refused"** (Redis): start Redis local (`docker run -p 6379:6379 redis`).
- **Tier 1 transcript fail** (YouTube 403): bình thường trên IP cloud — set `SUPADATA_API_KEY`.