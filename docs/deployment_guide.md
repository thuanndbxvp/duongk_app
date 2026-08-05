# Hướng dẫn Triển khai Kỹ thuật — YouTube AI SaaS

> **Stack chốt:** Ubuntu 24.04 VPS (SaaS core) + Supabase managed (Auth/DB) + Modal.com (GPU) + Cloudflare R2 (Object Storage)
> **Ngày phát hành:** 2026-08-05
> **Đối tượng:** Solo dev / small team triển khai MVP đến production

---

## Mục lục

1. [Kiến trúc tổng thể](#1-kiến-trúc-tổng-thể)
2. [Phần A — Setup CPU VPS Ubuntu 24.04](#2-phần-a--setup-cpu-vps-ubuntu-2404)
3. [Phần B — Setup Supabase managed](#3-phần-b--setup-supabase-managed)
4. [Phần C — Setup Cloudflare R2](#4-phần-c--setup-cloudflare-r2)
5. [Phần D — Setup Modal.com GPU](#5-phần-d--setup-modalcom-gpu)
6. [Phần E — Deploy application stack (Docker Compose)](#6-phần-e--deploy-application-stack-docker-compose)
7. [Phần F — Kết nối các thành phần (code integration)](#7-phần-f--kết-nối-các-thành-phần-code-integration)
8. [Phần G — Reverse proxy, SSL, domain](#8-phần-g--reverse-proxy-ssl-domain)
9. [Phần H — Monitoring, backup, security](#9-phần-h--monitoring-backup-security)
10. [Phần I — Deployment workflow & CI/CD](#10-phần-i--deployment-workflow--cicd)
11. [Phần J — Checklist go-live](#11-phần-j--checklist-go-live)

---

## 1. Kiến trúc tổng thể

```
User Browser
     │ HTTPS
     ▼
[Cloudflare DNS + Proxy]
     │
     ▼
[VPS Ubuntu 24.04]
├── Caddy (reverse proxy + auto SSL)
├── Next.js frontend      (port 3000)
├── FastAPI backend       (port 8000)
├── Celery worker (light) (background)
└── Redis                 (port 6379, internal)
     │
     ├──► Supabase managed   ← Auth + Postgres + RLS
     │
     ├──► Modal.com          ← GPU: FFmpeg render, Whisper, ML
     │       └──► Cloudflare R2 (upload output)
     │
     └──► Cloudflare R2      ← Serve output/media via CDN
```

**Nguyên tắc phân tách:**
- VPS chỉ giữ web/API/orchestration → nhẹ, nhanh
- Modal xử lý mọi thứ cần GPU/heavy compute
- R2 chỉ lưu media/output
- Supabase giữ source of truth cho user/credit/project

---

## 2. Phần A — Setup CPU VPS Ubuntu 24.04

### A.1 Bootstrap script

Chạy script này ngay sau khi provision VPS, dưới quyền `root`.

**File:** `bootstrap.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============ CONFIG ============
NEW_USER="deploy"
SSH_PUBKEY="ssh-ed25519 AAAA... your-key-here"
TIMEZONE="Asia/Ho_Chi_Minh"
SWAP_SIZE_GB=4
# ================================

echo "[1/10] Update system..."
apt-get update -y
apt-get upgrade -y

echo "[2/10] Set timezone..."
timedatectl set-timezone "$TIMEZONE"

echo "[3/10] Create user $NEW_USER..."
adduser --disabled-password --gecos "" "$NEW_USER"
usermod -aG sudo "$NEW_USER"
mkdir -p /home/$NEW_USER/.ssh
echo "$SSH_PUBKEY" > /home/$NEW_USER/.ssh/authorized_keys
chown -R $NEW_USER:$NEW_USER /home/$NEW_USER/.ssh
chmod 700 /home/$NEW_USER/.ssh
chmod 600 /home/$NEW_USER/.ssh/authorized_keys

echo "[4/10] Passwordless sudo for $NEW_USER..."
echo "$NEW_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$NEW_USER
chmod 440 /etc/sudoers.d/$NEW_USER

echo "[5/10] Hardening SSH..."
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl reload ssh

echo "[6/10] Setup firewall (ufw)..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "[7/10] Install fail2ban..."
apt-get install -y fail2ban
systemctl enable --now fail2ban

echo "[8/10] Setup swap ${SWAP_SIZE_GB}GB..."
if [ ! -f /swapfile ]; then
    fallocate -l ${SWAP_SIZE_GB}G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    sysctl -p
fi

echo "[9/10] Install Docker Engine..."
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
    > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker $NEW_USER

echo "[10/10] Install monitoring basics..."
apt-get install -y htop iotop ncdu jq unzip git

echo "✅ Bootstrap done. Logout and reconnect as: ssh $NEW_USER@$(curl -s ifconfig.me)"
```

**Cách chạy:**

```bash
# Từ máy local, upload lên VPS
scp bootstrap.sh root@YOUR_VPS_IP:/root/
ssh root@YOUR_VPS_IP
chmod +x /root/bootstrap.sh

# Sửa SSH_PUBKEY trong file trước
nano /root/bootstrap.sh
./bootstrap.sh

# Sau đó login lại với user deploy
ssh deploy@YOUR_VPS_IP
```

### A.2 Kiểm tra sau bootstrap

```bash
# Kiểm tra Docker
docker --version
docker compose version

# Kiểm tra swap
free -h

# Kiểm tra firewall
sudo ufw status

# Kiểm tra timezone
timedatectl
```

---

## 3. Phần B — Setup Supabase managed

### B.1 Tạo project

1. Đăng nhập [supabase.com](https://supabase.com)
2. New Project → chọn region **Southeast Asia (Singapore)** (gần VN nhất)
3. Đặt DB password mạnh, lưu vào password manager
4. Chờ ~2 phút cho project khởi tạo

### B.2 Lấy credentials cần thiết

Vào **Settings → API**:
- `SUPABASE_URL` = `https://xxxxx.supabase.co`
- `SUPABASE_ANON_KEY` = `eyJhbGc...` (dùng cho frontend)
- `SUPABASE_SERVICE_ROLE_KEY` = `eyJhbGc...` (dùng cho worker, KHÔNG expose frontend)

Vào **Settings → API → JWT Settings**:
- `SUPABASE_JWT_SECRET` (dùng cho FastAPI verify JWT)

### B.3 Chạy migrations

Sử dụng Supabase CLI:

```bash
# Trên máy local
npm install -g supabase
supabase login
supabase link --project-ref YOUR_PROJECT_REF

# Tạo migration đầu tiên
supabase migration new initial_schema
# Copy SQL từ Sprint 1 (users, jobs, credit_transactions, api_usage_logs)
# Paste vào file mới tạo trong supabase/migrations/

# Push lên Supabase
supabase db push
```

### B.4 Enable extensions cần thiết

Vào **Database → Extensions**, bật:
- `pgvector` (RAG embeddings)
- `pg_cron` (cleanup jobs)
- `uuid-ossp` (UUID generation)

### B.5 Cấu hình Auth

- **Authentication → Providers**: bật Email/Password
- **Authentication → URL Configuration**:
  - Site URL: `https://yourdomain.com`
  - Redirect URLs: `https://yourdomain.com/auth/callback`

---

## 4. Phần C — Setup Cloudflare R2

### C.1 Enable R2

1. Login [dash.cloudflare.com](https://dash.cloudflare.com)
2. Sidebar → **R2** → Enable (yêu cầu payment method, không bill nếu dưới 10 GB)

### C.2 Tạo buckets

Đặt tên rõ ràng, tách theo mục đích:

```
myapp-uploads       # user upload input
myapp-renders       # video output từ Modal
myapp-cache         # thumbnail, preview, cache tạm
myapp-backups       # database dump, snapshot
```

**Location:** Chọn **Automatic** (Cloudflare auto-optimize)

### C.3 Tạo API token

**R2 → Manage R2 API Tokens → Create API Token**:
- Permissions: `Object Read & Write`
- Bucket: chọn cả 4 bucket
- TTL: chọn không giới hạn cho backend (hoặc rotate 90 ngày)

Lưu lại:
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_ENDPOINT` = `https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com`

### C.4 Setup custom domain cho public bucket

Nếu muốn serve video output qua CDN:

**Bucket `myapp-renders` → Settings → Custom Domains → Connect Domain**
- Domain: `cdn.yourdomain.com`
- Cloudflare tự tạo DNS record + SSL

### C.5 Setup lifecycle rules

**Bucket `myapp-cache` → Settings → Lifecycle Rules**:
- Rule 1: Delete objects older than 7 days
- Rule 2: Delete incomplete multipart uploads after 1 day

**Bucket `myapp-uploads` → Settings → Lifecycle Rules**:
- Delete objects older than 30 days (nếu user không sync về project)

### C.6 Setup CORS (nếu upload trực tiếp từ browser)

**Bucket → Settings → CORS Policy**:

```json
[
  {
    "AllowedOrigins": ["https://yourdomain.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

---

## 5. Phần D — Setup Modal.com GPU

### D.1 Đăng ký & install CLI

```bash
# Trên máy local
pip install modal
modal token new
# Follow browser flow để authenticate
```

### D.2 Tạo Modal secrets

Modal cần biết credentials của R2 và các provider khác:

```bash
modal secret create r2-credentials \
    R2_ACCESS_KEY_ID="xxx" \
    R2_SECRET_ACCESS_KEY="xxx" \
    R2_ENDPOINT="https://xxx.r2.cloudflarestorage.com" \
    R2_BUCKET_RENDERS="myapp-renders"

modal secret create supabase-credentials \
    SUPABASE_URL="https://xxx.supabase.co" \
    SUPABASE_SERVICE_ROLE_KEY="eyJhbGc..."

modal secret create llm-keys \
    OPENAI_API_KEY="sk-..." \
    GEMINI_API_KEY="..."
```

### D.3 Modal app cho FFmpeg render

**File:** `modal_functions/render.py`

```python
import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "curl")
    .pip_install("boto3", "supabase", "requests")
)

app = modal.App("youtube-ai-render", image=image)

# Volume để cache font, assets tĩnh nếu cần
assets_volume = modal.Volume.from_name("render-assets", create_if_missing=True)

@app.function(
    gpu="T4",                    # dùng T4 cho render, đủ mạnh và rẻ
    timeout=1800,                # 30 phút max
    secrets=[
        modal.Secret.from_name("r2-credentials"),
        modal.Secret.from_name("supabase-credentials"),
    ],
    volumes={"/assets": assets_volume},
    min_containers=0,            # scale to 0 khi không dùng
)
def render_video(
    job_id: str,
    audio_url: str,
    scenes: list,               # [{footage_url, start, end, text}, ...]
    subtitle_srt: str,
    output_key: str,            # R2 key: renders/user_id/job_id.mp4
) -> dict:
    """Render final video from audio + footage + subtitle."""
    import os
    import subprocess
    import tempfile
    import boto3
    from supabase import create_client
    
    # 1. Update progress
    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    sb.table("jobs").update({"status": "running", "progress": 10}).eq("id", job_id).execute()
    
    with tempfile.TemporaryDirectory() as tmp:
        # 2. Download audio
        audio_path = f"{tmp}/audio.mp3"
        subprocess.run(["curl", "-sL", audio_url, "-o", audio_path], check=True)
        sb.table("jobs").update({"progress": 20}).eq("id", job_id).execute()
        
        # 3. Download footage cho từng scene
        footage_paths = []
        for i, scene in enumerate(scenes):
            path = f"{tmp}/footage_{i}.mp4"
            subprocess.run(["curl", "-sL", scene["footage_url"], "-o", path], check=True)
            footage_paths.append(path)
        sb.table("jobs").update({"progress": 40}).eq("id", job_id).execute()
        
        # 4. Ghi subtitle file
        srt_path = f"{tmp}/subs.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(subtitle_srt)
        
        # 5. Build concat list
        concat_path = f"{tmp}/concat.txt"
        with open(concat_path, "w") as f:
            for p in footage_paths:
                f.write(f"file '{p}'\n")
        
        # 6. Concat footage + overlay audio + burn subtitle với NVENC
        output_path = f"{tmp}/output.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-i", audio_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=20'",
            "-c:v", "h264_nvenc",       # GPU encode
            "-preset", "p4",
            "-b:v", "4M",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd, check=True)
        sb.table("jobs").update({"progress": 80}).eq("id", job_id).execute()
        
        # 7. Upload lên R2
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        s3.upload_file(output_path, os.environ["R2_BUCKET_RENDERS"], output_key)
        
        # 8. Generate public URL (dùng custom domain)
        public_url = f"https://cdn.yourdomain.com/{output_key}"
        
        # 9. Update job done
        sb.table("jobs").update({
            "status": "succeeded",
            "progress": 100,
            "result_payload": {"output_url": public_url, "size_bytes": os.path.getsize(output_path)}
        }).eq("id", job_id).execute()
        
        return {"status": "ok", "output_url": public_url}
```

**Deploy Modal function:**

```bash
cd modal_functions
modal deploy render.py
```

Sau khi deploy, function có endpoint và có thể gọi từ FastAPI qua `modal.Function.lookup()`.

### D.4 Modal app cho Whisper transcript

**File:** `modal_functions/transcribe.py`

```python
import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "curl")
    .pip_install("openai-whisper", "boto3", "supabase", "yt-dlp")
)

app = modal.App("youtube-ai-transcribe", image=image)

# Cache model weights giữa các invocation
model_cache = modal.Volume.from_name("whisper-models", create_if_missing=True)

@app.function(
    gpu="T4",
    timeout=1200,
    secrets=[
        modal.Secret.from_name("supabase-credentials"),
    ],
    volumes={"/root/.cache/whisper": model_cache},
    min_containers=0,
)
def transcribe_video(video_id: str, language: str = "vi") -> dict:
    import whisper
    import subprocess
    import tempfile
    import os
    from supabase import create_client
    
    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    
    with tempfile.TemporaryDirectory() as tmp:
        # Download audio
        audio_path = f"{tmp}/audio.mp3"
        subprocess.run([
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", audio_path,
            f"https://www.youtube.com/watch?v={video_id}"
        ], check=True)
        
        # Load model (cached in volume)
        model = whisper.load_model("medium")
        result = model.transcribe(audio_path, language=language, verbose=False)
        
        transcript = {
            "video_id": video_id,
            "language": result["language"],
            "source": "whisper",
            "text_content": result["text"],
            "timestamps": [
                {"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in result["segments"]
            ],
            "word_count": len(result["text"].split()),
        }
        
        sb.table("transcripts").upsert(transcript).execute()
        return transcript
```

---

## 6. Phần E — Deploy application stack (Docker Compose)

### E.1 Cấu trúc thư mục trên VPS

```
/home/deploy/myapp/
├── docker-compose.yml
├── .env
├── Caddyfile
├── apps/
│   ├── web/                 # Next.js
│   │   ├── Dockerfile
│   │   └── ...
│   ├── api/                 # FastAPI
│   │   ├── Dockerfile
│   │   └── ...
│   └── worker/              # Celery
│       ├── Dockerfile
│       └── ...
└── data/
    ├── redis/
    └── caddy/
```

### E.2 File `.env`

```bash
# ============ Supabase ============
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_JWT_SECRET=your-jwt-secret

# ============ Cloudflare R2 ============
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
R2_BUCKET_UPLOADS=myapp-uploads
R2_BUCKET_RENDERS=myapp-renders
R2_BUCKET_CACHE=myapp-cache
R2_PUBLIC_CDN=https://cdn.yourdomain.com

# ============ Modal ============
MODAL_TOKEN_ID=ak-xxx
MODAL_TOKEN_SECRET=as-xxx

# ============ Redis ============
REDIS_URL=redis://redis:6379/0

# ============ LLM providers ============
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=xxx
COHERE_API_KEY=xxx

# ============ App ============
DOMAIN=yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

**Bảo mật file:**

```bash
chmod 600 .env
```

### E.3 `docker-compose.yml`

```yaml
services:
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./data/caddy/data:/data
      - ./data/caddy/config:/config
    depends_on:
      - web
      - api

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      - NODE_ENV=production
      - PORT=3000
    expose:
      - "3000"
    depends_on:
      - api

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    expose:
      - "8000"
    depends_on:
      - redis

  worker:
    build:
      context: ./apps/worker
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    command: celery -A tasks worker --loglevel=info --concurrency=2
    depends_on:
      - redis

  scheduler:
    build:
      context: ./apps/worker
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    command: celery -A tasks beat --loglevel=info

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --save 60 1 --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - ./data/redis:/data
    expose:
      - "6379"

networks:
  default:
    name: myapp-network
```

### E.4 `Caddyfile`

```
yourdomain.com {
    encode gzip zstd
    
    # Frontend
    reverse_proxy web:3000
    
    # API routes
    handle /api/* {
        reverse_proxy api:8000
    }
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    
    # Logging
    log {
        output file /data/access.log {
            roll_size 100mb
            roll_keep 5
        }
    }
}
```

Caddy tự động lấy SSL từ Let's Encrypt, không cần certbot.

### E.5 Dockerfile cho từng app

**`apps/api/Dockerfile`:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**`apps/worker/Dockerfile`:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
```

**`apps/web/Dockerfile`** (Next.js standalone):

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && pnpm build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Trong `next.config.js`:

```javascript
module.exports = { output: 'standalone' };
```

---

## 7. Phần F — Kết nối các thành phần (code integration)

### F.1 FastAPI verify Supabase JWT

**`apps/api/deps.py`:**

```python
import os
import jwt
from fastapi import Depends, HTTPException, Header

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    
    token = authorization[7:]
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["exp", "sub", "aud"]}
        )
        return {"user_id": payload["sub"], "email": payload.get("email")}
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f"Invalid token: {e}")
```

### F.2 FastAPI gọi Modal function

**`apps/api/services/modal_client.py`:**

```python
import modal

def enqueue_render(job_id: str, audio_url: str, scenes: list, 
                   subtitle_srt: str, output_key: str):
    render_fn = modal.Function.lookup("youtube-ai-render", "render_video")
    call = render_fn.spawn(
        job_id=job_id,
        audio_url=audio_url,
        scenes=scenes,
        subtitle_srt=subtitle_srt,
        output_key=output_key,
    )
    return call.object_id  # Modal call ID, lưu vào jobs.celery_task_id
```

### F.3 FastAPI upload file lên R2

**`apps/api/services/r2_client.py`:**

```python
import os
import boto3
from botocore.config import Config

_s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["R2_ENDPOINT"],
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
    config=Config(signature_version="s3v4"),
)

def generate_presigned_upload_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )

def generate_presigned_download_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )

def public_url(key: str) -> str:
    return f"{os.environ['R2_PUBLIC_CDN']}/{key}"
```

### F.4 Endpoint tạo render job

**`apps/api/routers/render.py`:**

```python
from fastapi import APIRouter, Depends
from uuid import uuid4
from services.modal_client import enqueue_render
from services.credits import hold_credits
from services.supabase_client import get_supabase
from deps import get_current_user

router = APIRouter()

@router.post("/api/render/start")
async def start_render(body: dict, user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    project_id = body["project_id"]
    
    # Create job
    job_id = str(uuid4())
    sb = get_supabase()
    sb.table("jobs").insert({
        "id": job_id,
        "user_id": user_id,
        "task_type": "render_video",
        "status": "pending",
        "input_payload": {"project_id": project_id},
    }).execute()
    
    # Hold credits
    await hold_credits(user_id, cost=100, job_id=job_id)
    
    # Load project data
    project = sb.table("content_projects").select("*").eq("id", project_id).single().execute()
    
    # Enqueue Modal function
    output_key = f"renders/{user_id}/{job_id}.mp4"
    modal_call_id = enqueue_render(
        job_id=job_id,
        audio_url=project.data["audio_url"],
        scenes=project.data["scenes_data"],
        subtitle_srt=project.data["subtitle_srt"],
        output_key=output_key,
    )
    
    sb.table("jobs").update({"celery_task_id": modal_call_id}).eq("id", job_id).execute()
    
    return {"job_id": job_id, "status": "queued"}
```

### F.5 Frontend subscribe realtime progress

**`apps/web/components/render-progress.tsx`:**

```tsx
'use client';
import { useEffect, useState } from 'react';
import { createBrowserClient } from '@supabase/ssr';

export function RenderProgress({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<any>(null);
  
  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    
    supabase.from('jobs').select('*').eq('id', jobId).single()
      .then(({ data }) => setJob(data));
    
    const channel = supabase.channel(`render:${jobId}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'jobs',
        filter: `id=eq.${jobId}`,
      }, (payload) => setJob(payload.new))
      .subscribe();
    
    return () => { supabase.removeChannel(channel); };
  }, [jobId]);
  
  if (!job) return <div>Đang tải...</div>;
  
  return (
    <div>
      <div>Trạng thái: {job.status}</div>
      <progress value={job.progress} max={100} />
      {job.status === 'succeeded' && (
        <a href={job.result_payload.output_url} download>
          Tải video
        </a>
      )}
    </div>
  );
}
```

---

## 8. Phần G — Reverse proxy, SSL, domain

### G.1 Cấu hình DNS trên Cloudflare

Vào Cloudflare Dashboard → chọn domain → **DNS**:

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | @ | IP_VPS | 🟠 Proxied |
| A | www | IP_VPS | 🟠 Proxied |
| CNAME | cdn | (auto tạo khi setup R2 custom domain) | 🟠 Proxied |

### G.2 Cấu hình Cloudflare SSL

**SSL/TLS → Overview**: chọn **Full (strict)** vì Caddy có SSL Let's Encrypt.

**SSL/TLS → Edge Certificates**:
- Always Use HTTPS: ON
- Minimum TLS Version: 1.2

### G.3 Bảo vệ thêm bằng Cloudflare

- **Security → WAF**: bật rule managed default
- **Security → Bots**: bật Bot Fight Mode
- **Rules → Page Rules**: cache aggressive cho `/static/*`, `/cdn/*`

---

## 9. Phần H — Monitoring, backup, security

### H.1 Log collection

Cách đơn giản nhất: dùng [Better Stack](https://betterstack.com) free tier.

- Cài Vector agent trên VPS
- Ship logs Docker → Better Stack
- Setup alert khi error rate tăng

### H.2 Uptime monitoring

Dùng [UptimeRobot](https://uptimerobot.com) free tier:

- Monitor `https://yourdomain.com/api/health`
- Monitor `https://yourdomain.com/`
- Alert qua email/Telegram khi down > 2 phút

### H.3 Error tracking

**Sentry** (free tier 5k events/month):

```python
# Trong apps/api/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.environ.get("ENV", "production"),
)
```

Tương tự cho Next.js và Celery worker.

### H.4 Database backup

Supabase managed có backup tự động, nhưng nên có backup phụ:

**Cron job hàng ngày (VPS):**

```bash
# /home/deploy/backup.sh
#!/usr/bin/env bash
DATE=$(date +%Y%m%d)
pg_dump "$SUPABASE_DB_URL" | gzip > /tmp/backup-$DATE.sql.gz

# Upload lên R2
aws s3 cp /tmp/backup-$DATE.sql.gz s3://myapp-backups/db/ \
    --endpoint-url "$R2_ENDPOINT"

# Xóa file local
rm /tmp/backup-$DATE.sql.gz
```

```bash
# Crontab
0 3 * * * /home/deploy/backup.sh >> /var/log/backup.log 2>&1
```

### H.5 Security checklist

- [x] SSH key-only, disable root, disable password
- [x] UFW firewall chỉ mở 22/80/443
- [x] fail2ban chống brute force
- [x] `.env` chmod 600
- [x] Docker chạy dưới user không phải root
- [x] Supabase RLS enabled cho mọi bảng
- [x] JWT verify signature ở FastAPI
- [x] Rate limit ở Caddy hoặc FastAPI
- [x] Cloudflare WAF + Bot protection
- [x] R2 credentials rotate 90 ngày
- [x] Modal secrets không hardcode

---

## 10. Phần I — Deployment workflow & CI/CD

### I.1 Manual deployment (đơn giản nhất)

```bash
# Trên máy local
git push origin main

# SSH vào VPS
ssh deploy@your-vps

cd ~/myapp
git pull
docker compose build
docker compose up -d
docker compose logs -f --tail 50
```

### I.2 GitHub Actions CI/CD

**`.github/workflows/deploy.yml`:**

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: deploy
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/myapp
            git pull origin main
            docker compose build
            docker compose up -d
            docker system prune -f
      
      - name: Deploy Modal functions
        env:
          MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
          MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
        run: |
          pip install modal
          modal deploy modal_functions/render.py
          modal deploy modal_functions/transcribe.py
```

### I.3 Zero-downtime deploy

Với Caddy + Docker, có thể dùng chiến lược:

```bash
# Blue-green deploy đơn giản
docker compose up -d --no-deps --scale api=2 api
sleep 10
docker compose up -d --no-deps --scale api=1 api
```

Hoặc dùng Coolify để có UI quản lý deploy đẹp hơn:

```bash
# Cài Coolify
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

---

## 11. Phần J — Checklist go-live

### Trước khi launch

**Infrastructure:**

- [ ] VPS Ubuntu 24.04 đã bootstrap
- [ ] Docker, Docker Compose hoạt động
- [ ] Firewall enabled, chỉ mở 22/80/443
- [ ] Swap 4 GB
- [ ] Backup script hàng ngày

**Supabase:**

- [ ] Project tạo ở region SG
- [ ] Migrations pushed
- [ ] RLS enabled cho mọi bảng
- [ ] Auth email/password bật
- [ ] Extensions: pgvector, pg_cron

**Cloudflare R2:**

- [ ] 4 buckets tạo
- [ ] API token
- [ ] Custom domain `cdn.yourdomain.com`
- [ ] Lifecycle rules cho cache/uploads
- [ ] CORS policy nếu cần

**Modal:**

- [ ] Account đã setup
- [ ] Secrets đã tạo (R2, Supabase, LLM)
- [ ] Functions deploy: render, transcribe
- [ ] Test call thành công

**Application:**

- [ ] `.env` đầy đủ, chmod 600
- [ ] `docker compose up -d` chạy sạch
- [ ] Web accessible qua HTTPS
- [ ] API healthcheck xanh
- [ ] Realtime subscription hoạt động
- [ ] Credit hold/commit/release test pass
- [ ] Render end-to-end test 1 video thành công

**Monitoring:**

- [ ] Sentry integrated
- [ ] Uptime monitoring bật
- [ ] Log shipping hoạt động
- [ ] Alert email/Telegram cấu hình

**Security:**

- [ ] SSH key-only
- [ ] fail2ban chạy
- [ ] Cloudflare WAF bật
- [ ] Rate limit test
- [ ] Secrets không có trong git

**Business:**

- [ ] Terms of Service, Privacy Policy
- [ ] Payment gateway (nếu có)
- [ ] Landing page
- [ ] User onboarding flow

---

## Tổng kết

Stack cuối cùng của bạn:

```
Ubuntu 24.04 VPS (2C/4G)      → SaaS core, orchestration
    + Supabase managed         → Auth, DB, RLS, Realtime
    + Modal.com                → GPU: FFmpeg render, Whisper, ML
    + Cloudflare R2            → Object storage, CDN, egress free
    + Cloudflare DNS/WAF       → Security, edge
    + Sentry + UptimeRobot     → Monitoring
```

Đây là một **kiến trúc modern, cost-efficient, ít ops**, phù hợp cho SaaS bắt đầu launch.

Chi phí dự kiến cho MVP (~50 video/tháng): **$20–60/tháng**.

Khi scale lên 500 video/tháng: **$150–250/tháng**, vẫn rẻ hơn rất nhiều so với dedicated GPU 24/7 + S3 egress.
