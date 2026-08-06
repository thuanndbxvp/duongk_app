# Bối cảnh Hệ thống (CONTEXT): phase3-env-docs

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md` (mục 1.4 "Env & Secrets" + STT #14 ".env.example bổ sung R2/MODAL/SUPADATA/SERPAPI/STALI").
- **Hiện trạng `.env.example`:** 19 dòng. **THIẾU** 11 biến quan trọng.
- **Hiện trạng `.env`:** 36 dòng, đã có R2/MODAL/STALI (đa số là PLACEHOLDER) + Supabase + Redis. **THIẾU** OPENAI/COHERE/YOUTUBE/SUPADATA/SERPAPI/SENTRY/ADMIN_ALLOWED_IPS/CELERY_*/PYTHONUNBUFFERED.

## 2. Codebase Analysis (qua Read + Grep)

### `.env.example` hiện tại (19 dòng)
```
YOUTUBE_API_KEY_1=...
OPENAI_API_KEY=...
COHERE_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SUPABASE_JWT_SECRET=your-jwt-secret-here1
SENTRY_DSN=...
ADMIN_ALLOWED_IPS=127.0.0.1,::1
```

### Các consumer biến môi trường (xác nhận qua Grep)
| Biến | Consumer file | Bắt buộc? |
|------|---------------|------------|
| `R2_*` | `apps/api/modules/voice/routes.py` (boto3 client cho TTS upload) | Có — Phase 5 TTS đang chạy |
| `MODAL_TOKEN_*` | `apps/worker/services/omnivoice_client.py` (Modal client cho TTS synthesize) | Có — TTS đang chạy |
| `SUPADATA_API_KEY` | `apps/api/modules/transcript/engine.py` (Tier 2 fallback) | Có — Tier 1 hay 403 trên IP cloud |
| `SERPAPI_KEY` | `apps/api/modules/module_1/service.py` (Pytrends fallback) | Có — Pytrends từ cloud IP fail |
| `STALI_*` | KHÔNG có consumer trong code (audit 1.4 ghi "code không dùng tới") | **Optional** — note trong ENV-VARS.md |
| `OPENAI_API_KEY` | `apps/api/services/credit_manager.py` (không trực tiếp — qua worker), `apps/worker/tasks/*.py` | Có |
| `COHERE_API_KEY` | `apps/api/modules/rag/embedder.py` | Có — nếu không dùng embedding |
| `YOUTUBE_API_KEY_1` | `apps/api/modules/module_2a/service.py:YouTubeCollector` | Có — không có sẽ fail Phase 1 collect_channel_task |
| `SENTRY_DSN` | `apps/api/main.py:27` (`sentry_sdk.init`) | Optional — nếu None thì Sentry no-op |
| `SUPABASE_JWT_SECRET` | `apps/api/dependencies/auth.py` (verify JWT) | Có |
| `ADMIN_ALLOWED_IPS` | Đã có trong Phase 5 plan admin | Có — nếu dùng admin |
| `PYTHONUNBUFFERED` | `docker-compose.prod.yml` (set trực tiếp) | Optional cho local |

### Files KHÔNG tồn tại (cần tạo mới)
- `docs/SETUP.md` — Hướng dẫn setup từ zero.
- `docs/ENV-VARS.md` — Liệt kê từng biến + cách lấy.
- `scripts/check-env.py` — Script verify env.

### Files cần UPDATE
- `.env.example` — Thêm 11 biến.
- `apps/web/README.md` — Có sẵn (Next.js default). Append 1 section "Environment".

### Files KHÔNG đụng
- `.env` (local) — Tier 2 KHÔNG sửa file này (chứa secret thật).
- `docker-compose*.yml` — Đang set env đúng.
- Mọi file code khác (Phase 3 không đụng logic).

## 3. Các File liên quan và Vai trò

| File | Vai trò |
|------|---------|
| `.env.example` | Template cho dev copy thành `.env`. PHẢI có đủ biến, không có giá trị thật. |
| `.env` (KHÔNG đụng) | File local chứa secret thật. Tier 2 KHÔNG commit file này. |
| `docs/SETUP.md` | Hướng dẫn setup 5 phút: clone → install → copy env → start. |
| `docs/ENV-VARS.md` | Bảng chi tiết từng biến: tên, mô tả, nguồn lấy, ví dụ. |
| `scripts/check-env.py` | Script verify: in OK cho từng required var có giá trị, in MISSING cho var trống. |
| `apps/web/README.md` | Append section env (giữ nguyên phần Next.js default). |

## 4. Dependencies
- **External:** Không thêm package mới.
- **Internal:** `python-dotenv` đã có (load `.env` tự động qua `load_dotenv`).

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Không commit secret thật:** `.env.example` chỉ chứa placeholder (`...` hoặc `PLACEHOLDER_*`).
- **Không đụng `.env`:** Tier 2 KHÔNG sửa `.env` local.
- **Không đụng `docker-compose*.yml`:** Env đã set đúng.
- **Backward compatible:** Khi thêm biến mới, code phải handle None gracefully (đã có sẵn qua `os.getenv('KEY')`).

## 6. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- `.env.example` có đủ 30 dòng (19 cũ + 11 mới).
- `docs/SETUP.md` + `docs/ENV-VARS.md` + `scripts/check-env.py` tồn tại.
- `python scripts/check-env.py` in được danh sách 30 biến, OK cho tất cả required.
- `apps/web/README.md` có section env mới.