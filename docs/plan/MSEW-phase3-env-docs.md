# MSEW: phase3-env-docs

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase3-env-docs.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase3-env-docs.md`
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF
- **Quy tắc:** KHÔNG commit secret thật vào `.env.example`. KHÔNG sửa `.env` local.

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | UPDATE `.env.example` (thêm 11 biến) | `devops` | `docs-manager` | `debugging` |
| 2 | Tạo `docs/SETUP.md` | `docs-manager` | `devops` | `code-review` |
| 3 | Tạo `docs/ENV-VARS.md` | `docs-manager` | `devops` | `code-review` |
| 4 | Tạo `scripts/check-env.py` | `devops` | `debugging` | `code-review` |
| 5 | UPDATE `apps/web/README.md` (append env section) | `docs-manager` | `frontend-development` | `devops` |
| 6 | Self-verify toàn bộ | `debugging` | `code-review` | `devops` |

## Files KHÔNG được đụng (Do Not Touch)
- `.env` (local) — chứa secret thật.
- `docker-compose*.yml`.
- Tất cả file code Python/TypeScript ngoài `scripts/check-env.py`.

---

## Micro-Steps

### Step 1: UPDATE `.env.example` (thêm 11 biến)
**File:** `.env.example` (UPDATE — replace toàn bộ file)
**Vị trí:** Toàn bộ 19 dòng hiện tại + 11 dòng mới.
**Skill Invocation:**
  - **Primary:** `devops`.
  - **Reference:** `docs-manager`.
  - **Fallback:** `debugging`.

**Pre-check:**
- File hiện tại đã đọc trong CONTEXT (19 dòng).

**Code cần viết (replace_all — ghi đè toàn bộ):**

```bash
# === Supabase ===
YOUTUBE_API_KEY_1=...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_JWT_SECRET=your-jwt-secret-from-dashboard

# === Redis ===
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# === Cloudflare R2 (used by voice/TTS upload + render) ===
R2_ACCESS_KEY_ID=PLACEHOLDER_R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY=PLACEHOLDER_R2_SECRET_ACCESS_KEY
R2_ENDPOINT=https://PLACEHOLDER_ACCOUNT_ID.r2.cloudflarestorage.com
R2_BUCKET_UPLOADS=appdk-uploads
R2_BUCKET_RENDERS=appdk-renders
R2_BUCKET_CACHE=appdk-cache
R2_PUBLIC_CDN=https://appdk-uploads.YOUR_SUBDOMAIN.r2.dev

# === Modal (used by TTS synthesize) ===
MODAL_TOKEN_ID=PLACEHOLDER_TOKEN_ID
MODAL_TOKEN_SECRET=PLACEHOLDER_TOKEN_SECRET

# === LLM providers ===
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...

# === External APIs ===
SUPADATA_API_KEY=...   # Tier 2 transcript fallback
SERPAPI_KEY=...         # Pytrends fallback for niche validation

# === Stali (optional — currently unused in code) ===
STALI_API_KEY=...
STALI_BASE_URL=https://api.stali.vn/v1

# === Observability ===
SENTRY_DSN=

# === Admin panel ===
ADMIN_ALLOWED_IPS=127.0.0.1,::1

# === App ===
ENV=development
NODE_ENV=development
PYTHONUNBUFFERED=1
```

**KHÔNG được sửa:**
- Không commit giá trị thật.
- Không thêm comment có chứa key thật.

**Verify command:**
```powershell
Get-Content .env.example | Measure-Object -Line
Select-String -Path .env.example -Pattern "^[A-Z_]+="
```

**Expected output:** Line count ≥ 30. Count pattern `^[A-Z_]+=` = 30.

---

### Step 2: Tạo `docs/SETUP.md`
**File:** `docs/SETUP.md` (NEW)
**Skill Invocation:**
  - **Primary:** `docs-manager`.
  - **Reference:** `devops`.
  - **Fallback:** `code-review`.

**Code cần viết:**

```markdown
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
```

**Verify command:**
```powershell
Get-Content docs\SETUP.md | Measure-Object -Line
```

**Expected output:** Line count ≥ 60.

---

### Step 3: Tạo `docs/ENV-VARS.md`
**File:** `docs/ENV-VARS.md` (NEW)
**Skill Invocation:**
  - **Primary:** `docs-manager`.
  - **Reference:** `devops`.
  - **Fallback:** `code-review`.

**Code cần viết:**

```markdown
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
```

**Verify command:**
```powershell
Get-Content docs\ENV-VARS.md | Measure-Object -Line
```

**Expected output:** Line count ≥ 80.

---

### Step 4: Tạo `scripts/check-env.py`
**File:** `scripts/check-env.py` (NEW)
**Skill Invocation:**
  - **Primary:** `devops`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

```python
"""
Verify environment variables for AppDK development.
Run: python scripts/check-env.py
"""
import os
import sys
from pathlib import Path


# Load .env nếu có (optional — Tier 2 có thể chạy trước khi copy env)
ENV_FILE = Path(__file__).parent.parent / '.env'
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())


# Required vars + optional flag
VARS = [
    # (name, required, description)
    ('SUPABASE_URL', True, 'Project URL'),
    ('SUPABASE_ANON_KEY', True, 'Public anon key'),
    ('SUPABASE_SERVICE_ROLE_KEY', True, 'Server-side key'),
    ('SUPABASE_JWT_SECRET', True, 'JWT verification secret'),
    ('NEXT_PUBLIC_SUPABASE_URL', True, 'Mirror for Next.js'),
    ('NEXT_PUBLIC_SUPABASE_ANON_KEY', True, 'Mirror for Next.js'),
    ('REDIS_URL', True, 'Redis connection'),
    ('CELERY_BROKER_URL', True, 'Celery broker'),
    ('CELERY_RESULT_BACKEND', True, 'Celery result backend'),
    ('OPENAI_API_KEY', True, 'OpenAI GPT-4o, Whisper'),
    ('COHERE_API_KEY', True, 'Cohere Embed v3'),
    ('YOUTUBE_API_KEY_1', True, 'YouTube Data API v3'),
    ('SUPADATA_API_KEY', True, 'Tier 2 transcript fallback'),
    ('SERPAPI_KEY', True, 'Pytrends fallback'),
    ('R2_ACCESS_KEY_ID', True, 'Cloudflare R2 token'),
    ('R2_SECRET_ACCESS_KEY', True, 'Cloudflare R2 token secret'),
    ('R2_ENDPOINT', True, 'R2 endpoint URL'),
    ('R2_BUCKET_UPLOADS', True, 'R2 uploads bucket'),
    ('R2_BUCKET_RENDERS', True, 'R2 renders bucket'),
    ('R2_BUCKET_CACHE', True, 'R2 cache bucket'),
    ('R2_PUBLIC_CDN', True, 'R2 public CDN URL'),
    ('MODAL_TOKEN_ID', True, 'Modal auth token ID'),
    ('MODAL_TOKEN_SECRET', True, 'Modal auth token secret'),
    # Optional
    ('SENTRY_DSN', False, 'Error tracking (optional)'),
    ('ADMIN_ALLOWED_IPS', False, 'Admin IP whitelist (defaults to 127.0.0.1)'),
    ('STALI_API_KEY', False, 'Stali LLM (optional — unused)'),
    ('STALI_BASE_URL', False, 'Stali base URL (optional)'),
    ('PYTHONUNBUFFERED', False, 'Python log flush (set to 1)'),
    ('ENV', False, 'App environment (development/production)'),
    ('NODE_ENV', False, 'Node environment'),
]


def main() -> int:
    print('AppDK — Environment Check')
    print('=' * 70)
    print(f'{"Variable":<35} {"Status":<10} {"Description"}')
    print('-' * 70)
    
    missing_required = 0
    
    for name, required, description in VARS:
        value = os.environ.get(name)
        if value:
            # Mask secret keys (chỉ hiện prefix + ***)
            if any(k in name.upper() for k in ('KEY', 'SECRET', 'TOKEN', 'PASSWORD')):
                masked = value[:4] + '***' if len(value) > 4 else '***'
                status = f'[OK] {masked}'
            else:
                status = f'[OK] {value[:30]}'
        else:
            status = '[MISSING]' if required else '[OPTIONAL]'
            if required:
                missing_required += 1
        
        print(f'{name:<35} {status:<10} {description}')
    
    print('-' * 70)
    
    if missing_required == 0:
        print(f'\n✓ All {len(VARS)} variables checked. {sum(1 for _, r, _ in VARS if r)} required — all present.')
        return 0
    else:
        print(f'\n✗ {missing_required} required variable(s) MISSING.')
        print('  → Xem docs/ENV-VARS.md để biết cách lấy.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

**Verify command:**
```powershell
cd d:\appDK
python scripts\check-env.py
```

**Expected output:** Bảng 30 biến, status `[OK]` cho tất cả required, `[OPTIONAL]` cho optional. Có thể có `[MISSING]` nếu `.env` local chưa đủ.

---

### Step 5: UPDATE `apps/web/README.md` (append env section)
**File:** `apps/web/README.md` (UPDATE — append cuối file)
**Vị trí:** Cuối file (sau section Next.js default).
**Skill Invocation:**
  - **Primary:** `docs-manager`.
  - **Reference:** `frontend-development`.
  - **Fallback:** `devops`.

**Pre-check:**
- File có sẵn (Next.js default README).

**Code cần viết (append vào cuối file):**

```markdown

---

## Environment Variables

Web app cần các biến `NEXT_PUBLIC_SUPABASE_URL` và `NEXT_PUBLIC_SUPABASE_ANON_KEY` trong `.env` (root repo).

Xem chi tiết từng biến tại [`docs/ENV-VARS.md`](../../docs/ENV-VARS.md) và hướng dẫn setup tại [`docs/SETUP.md`](../../docs/SETUP.md).

Để verify env:
```bash
python scripts/check-env.py
```
```

**KHÔNG được sửa:**
- Phần Next.js default (heading, Getting Started, Learn More...).
- Không chạy `create-next-app` lại.

**Verify command:**
```powershell
Get-Content apps\web\README.md | Select-String "Environment Variables|ENV-VARS|SETUP" | Measure-Object -Line
```

**Expected output:** Count ≥ 3.

---

### Step 6: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `devops`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) .env.example có 30 biến
$envExample = (Get-Content .env.example | Select-String "^[A-Z_]+=" | Measure-Object -Line).Lines
Write-Host ".env.example variables: $envExample"

# 2) Không có secret leak trong .env.example
$secrets = Select-String -Path .env.example -Pattern "sk-[a-zA-Z]|eyJ[a-zA-Z]|PLACEHOLDER_R2.*ACCESS|R2.*SECRET.*[a-zA-Z0-9]{20,}" | Measure-Object -Line
Write-Host "Suspicious secrets in .env.example: $secrets.Lines"

# 3) 3 file docs/scripts tồn tại
Test-Path docs\SETUP.md
Test-Path docs\ENV-VARS.md
Test-Path scripts\check-env.py

# 4) check-env.py chạy được
python scripts\check-env.py | Select-Object -Last 5

# 5) apps/web/README.md có section env
$readmeHits = (Get-Content apps\web\README.md | Select-String "Environment Variables" | Measure-Object -Line).Lines
Write-Host "web README env mentions: $readmeHits"
```

**Expected output:**
- `.env.example variables: 30`
- `Suspicious secrets: 0`
- 3 file đều `True`
- check-env.py in bảng 30 biến
- `web README env mentions: 1` (hoặc hơn)

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`.
- Ghi vào `BLOCKERS.md`.

---

## Definition of Done cho Phase này
- `.env.example` có ≥ 30 biến, KHÔNG chứa secret thật.
- `docs/SETUP.md` + `docs/ENV-VARS.md` + `scripts/check-env.py` tồn tại.
- `python scripts/check-env.py` chạy được, in bảng 30 biến.
- `apps/web/README.md` có section env (≥ 1 mention "Environment Variables").
- KHÔNG file `.env` local nào bị sửa.
- KHÔNG file code nào ngoài `scripts/check-env.py` bị đụng.