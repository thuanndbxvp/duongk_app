# 🚀 QUICK RUN & ONBOARDING PLAYBOOK — AI86 (appDK)

> **MỤC ĐÍCH FILE NÀY**: Dành cho bất kỳ **AI Coding Assistant** hoặc **Developer** mới nào join dự án. Đọc file này để nắm ngay cách chạy, kiểm thử, vận hành và triển khai hệ thống mà không làm gãy kiến trúc.
>
> 📖 *Để hiểu sâu về kiến trúc tổng thể, sơ đồ dữ liệu và quy chuẩn kỹ thuật, xem thêm:* [STACK.md](file:///D:/appDK/docs/important/STACK.md)

---

## 1. ⚡ Quick Overview: Dự án này là gì?
- **Tên dự án**: `appDK` (Ecosystem AI86 / `ai86.click`) — Nền tảng SaaS sáng tạo nội dung, sản xuất video tự động, Voice Cloning và SRT Dubbing chuyên nghiệp.
- **Các domain đang chạy**:
  - `https://ai86.click` & `www.ai86.click`: Web App giao diện chính (Next.js 15).
  - `https://api.ai86.click`: REST API Backend chính (FastAPI).
  - `https://voice.ai86.click`: Voice Studio (TTS & SRT Dubbing Dashboard - OmniVoice).
  - `https://cdn.ai86.click`: CDN Public Media (Cloudflare R2).
- **Hạ tầng chính**:
  - **CPU VPS (Production)**: `161.248.4.99` (Ubuntu 24.04, Docker Compose tại `/opt/appdk`).
  - **Serverless GPU**: Modal.com (`ai-dubbing-pipeline`).
  - **Database & Auth**: Supabase Managed (Postgres 15 + RLS + Realtime).
  - **Object Storage (Cloudflare R2)**:
    - `appdk-uploads`: Chứa file audio/video mẫu, input của người dùng.
    - `appdk-renders`: Chứa audio output TTS, file lồng tiếng SRT dubbing.
    - `appdk-cache`: Chứa cache tạm, thumbnail, preview.

---

## 2. 📂 Cấu Trúc Monorepo & Phân Công Nhiệm Vụ

| Thư mục / Service | Công nghệ | Nhiệm vụ & Quy tắc |
|---|---|---|
| `apps/web` | Next.js 15, React 19, Tailwind, shadcn/ui | Giao diện người dùng chính. **BFF Pattern**: Browser gọi Next.js route handlers, Next.js chuyển tiếp sang FastAPI. |
| `apps/api` | FastAPI (Python 3.12), Pydantic v2 | REST API nghiệp vụ (`modules/rag`, `modules/analysis`, `modules/transcript`, `modules/voice`...). |
| `apps/worker` | Celery 5.4 + Redis 7 | Chạy các tác vụ background nặng: script generation, NLP, analysis fan-out. |
| `apps/omnivoice` | FastAPI + HTML5/JS (Port 8088) | Phục vụ domain `voice.ai86.click`. Quản lý danh mục voice (`voice_registry.json`), file mẫu (`voices/`), giao diện TTS & SRT Dubbing. |
| `modal_functions/` | Modal Python SDK | Serverless GPU (A10G/T4) chạy model OmniVoice (`synthesize_voice`, `dub_srt` lồng tiếng phụ đề SRT). |
| `supabase/` | Postgres SQL Migrations | Bảng dữ liệu, RLS policies, views, `api_provider_keys` (Vault mã hóa key). |

---

## 3. ⚖️ 5 Nguyên Tắc Bất Di Bất Dịch (Anti-Patterns)

1. ❌ **KHÔNG BAO GIỜ nhét LLM/AI Provider API Keys vào `.env`**: Mọi key (OpenAI, Gemini, Groq, Cohere...) được lưu trong bảng `api_provider_keys` (Supabase Vault) và đọc qua `key_resolver`.
2. ❌ **KHÔNG chạy AI nặng hoặc FFmpeg Encode trên CPU VPS**: CPU VPS chỉ làm web/API/orchestration. Việc nặng chuyển sang Modal GPU hoặc GPU worker.
3. ❌ **KHÔNG lưu media/render lâu dài trên ổ cứng local của VPS**: Luôn đẩy lên Cloudflare R2 (`appdk-uploads`, `appdk-renders`, `appdk-cache`).
4. ❌ **KHÔNG xóa các giọng hệ thống (`is_system = true`)**: Các voice gốc (`ban_mai`, `thao_trinh`, `ngoc_huyen`, `lan_trinh`, `tuong_vy`, `ngan_ha`, `minhquan_vb`, `ngochuyen_vb`) được bảo vệ ở cả Backend lẫn UI.
5. ❌ **KHÔNG khóa cứng seed (`torch.manual_seed`) khi sinh TTS giọng clone**: Khóa seed lặp lại sẽ gây lỗi lặp từ / nói lắp (autoregressive hallucinations).

---

## 4. 🔄 Quy Trình Push - Pull - Go-Live lên CPU VPS (Deployment Runbook)

### 💡 Nguyên lý Go-Live trên Production:
Trên CPU VPS (`161.248.4.99`), toàn bộ dịch vụ (`api`, `web`, `omnivoice`, `worker_*`) chạy dưới dạng **Docker containers độc lập** và source code đã được **bake trực tiếp vào Docker image** (không mount live code để đảm bảo an toàn & hiệu năng).

```
[Máy Local (D:\appDK)]       [GitHub: main]              [CPU VPS: 161.248.4.99]
        │                           │                               │
 1. git push ──────────────────────►│                               │
                                    │ 2. python update.py ─────────►│ (SSH tự động)
                                    │                               │ 3. cd /opt/appdk && git pull
                                    │                               │ 4. docker compose up -d --build <service>
                                    │                               │ 5. Container cập nhật & Go-Live!
```

---

### 📌 Bảng Tra Cứu: Sửa File Nào ➔ Chạy Lệnh Gì?

| Khu vực vừa sửa code | Service liên quan | Lệnh Go-Live cần chạy |
|---|---|---|
| `apps/omnivoice/` (Web UI, catalog, TTS API) | `omnivoice` (`voice.ai86.click`) | `python update.py` *(hoặc `python update.py omnivoice`)* |
| `apps/api/` (FastAPI backend endpoints) | `api` (`api.ai86.click`) | `python update.py api` |
| `apps/web/` (Giao diện Next.js chính) | `web` (`ai86.click`) | `python update.py web` |
| `apps/worker/` (Celery background tasks) | `worker_*` (ML, high, io, normal) | `python update.py all` |
| `modal_functions/` (Serverless GPU model) | Modal.com Cloud | `$env:PYTHONUTF8=1; modal deploy modal_functions/dubbing_pipeline.py` |
| `supabase/migrations/` | Supabase Postgres DB | Chạy SQL trên Supabase Dashboard / Migration CLI |

---

### A. Cách 1: Tự động 1-Click bằng script `update.py` (Khuyên dùng):
Chỉ cần mở terminal tại thư mục gốc dự án (`D:\appDK`) và chạy:

```powershell
# Bước 1: Commit và Push code lên GitHub
git add .
git commit -m "feat/fix: mô tả nội dung vừa sửa"
git push

# Bước 2: Kích hoạt cập nhật tự động lên VPS:
python update.py           # Mặc định: Rebuild container omnivoice (voice.ai86.click)
python update.py api       # Rebuild container backend api (api.ai86.click)
python update.py web       # Rebuild container frontend web (ai86.click)
python update.py all       # Rebuild và khởi động lại toàn bộ services
```

---

### B. Cách 2: Thao tác thủ công qua SSH (Khi cần debug trực tiếp):
```bash
# 1. SSH vào VPS:
ssh deploy@161.248.4.99
# Password: hJ%ExH;V_#|6

# 2. Di chuyển vào thư mục dự án và kéo code mới:
cd /opt/appdk
git pull origin main

# 3. Rebuild và chạy container tương ứng:
# Rebuild riêng service omnivoice:
docker compose -f docker-compose.prod.yml up -d --build omnivoice

# Hoặc rebuild riêng api/web:
docker compose -f docker-compose.prod.yml up -d --build api
docker compose -f docker-compose.prod.yml up -d --build web

# 4. Kiểm tra trạng thái container:
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f --tail=50 omnivoice
```

---

### C. Triển khai Modal GPU Pipeline (`modal_functions/`):
Khi chỉnh sửa logic inference AI trong `modal_functions/dubbing_pipeline.py`:
```powershell
$env:PYTHONUTF8=1; modal deploy modal_functions/dubbing_pipeline.py
```

---

### D. Xem Logs & Kiểm tra trạng thái từ xa:
```powershell
# Xem log container OmniVoice (voice.ai86.click)
python -c "import paramiko, sys; sys.stdout.reconfigure(encoding='utf-8'); ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()); ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6'); _, out, _ = ssh.exec_command('docker logs appdk-omnivoice-1 --tail 50'); print(out.read().decode('utf-8')); ssh.close()"

# Xem log Caddy reverse proxy
python -c "import paramiko, sys; sys.stdout.reconfigure(encoding='utf-8'); ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()); ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6'); _, out, _ = ssh.exec_command('docker logs appdk-caddy-1 --tail 50'); print(out.read().decode('utf-8')); ssh.close()"
```

---

## 5. 🧪 Kiểm Thử Nhanh (Smoke Test Cheatsheet)

### Test nhanh TTS endpoint trên Production:
```powershell
python -c "import requests; r = requests.post('https://voice.ai86.click/v1/tts', json={'text': 'Xin chào, đây là kiểm tra hệ thống.', 'voice_id': 'ban_mai'}); print('Status:', r.status_code, '| Bytes:', len(r.content))"
```

### Test Catalog Voices:
```powershell
python -c "import requests; r = requests.get('https://voice.ai86.click/v1/catalog'); print('Total voices:', len(r.json().get('voices', [])))"
```

---

## 6. 🛠️ Quy Trình Phối Hợp 2 Tầng (2-Tier AI Pipeline)
- **Tầng 1 (Architect / Planner)**: Phân tích yêu cầu của sếp, nghiên cứu context, thiết kế bản vẽ kỹ thuật chi tiết (`docs/plans/`).
- **Tầng 2 (Coder / Autonomous Engineer)**: Đối chiếu code hiện tại (Pre-Audit), thực thi code chính xác theo bản vẽ, tự chạy test và audit lint/syntax trước khi báo cáo hoàn thành.
