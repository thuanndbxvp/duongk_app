# Bối cảnh Hệ thống (CONTEXT): phase7-admin-api-keys

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A3)
- **Phase 5 đã viết xong:** `require_admin` + `audit.py:log_admin_action` + migration 0022.
- **Phase 6 đã viết plan** (chưa thực thi): 3 routers admin (users/credit/pricing) + 3 trang admin UI.
- **Đây là Sprint A3:** API Key Management theo checklist 2.7.

## 2. Codebase Analysis (qua Read + Grep)

### Discovery — Phase 6 đã chuẩn bị nền tảng
- **`apps/api/routers/admin_users.py`** (Phase 6 plan) — có `Depends(require_admin)` + `log_admin_action`.
- **`apps/api/services/audit.py:12`** — `_SENSITIVE_KEYS` regex `(key|token|secret|password|api_key)` mask tự động trong `before`/`after`.
- **`apps/web/app/(admin)/layout.tsx`** — sidebar có `API Keys.enabled = false` (Phase 6 chưa enable).

### Hiện trạng consumers (qua Grep)
| File | Provider | Cách lấy key hiện tại |
|------|----------|------------------------|
| `apps/api/modules/voice/routes.py:16-18` | R2 | `os.environ["R2_*"]` trực tiếp |
| `apps/worker/services/omnivoice_client.py` | Modal | `modal` SDK lookup (dùng `MODAL_TOKEN_*`) |
| `apps/api/services/credit_manager.py` | OpenAI | Đã có `OpenAI(api_key=os.environ["OPENAI_API_KEY"])` |
| `apps/api/modules/rag/embedder.py` | Cohere | `os.environ["COHERE_API_KEY"]` |
| `apps/api/modules/transcript/engine.py` | Supadata | `os.environ["SUPADATA_API_KEY"]` |
| `apps/api/modules/module_1/service.py` | SerpAPI | `os.environ["SERPAPI_KEY"]` |

### Pattern consumer hiện tại
- **Không có `key_resolver` service.** Mỗi module đọc trực tiếp `os.environ`.
- Phase 7 cần tạo `apps/api/services/key_resolver.py` (lookup + cache 60s + fallback chain).

### Database schema cần thêm
- **CHƯA CÓ** bảng `api_provider_keys` (admin_panel_plan.md mục 2.3 đã design nhưng chưa apply).
- **CHƯA CÓ** bảng `api_usage_logs` (cost tracking).
- **CHƯA CÓ** bảng `admin_alerts` (alert generator).
- **CHƯA CÓ** migration 0023+. (Last migration: `0022_admin_panel_foundation.sql`).

### Files KHÔNG tồn tại (cần tạo mới)
- `supabase/migrations/0023_api_provider_keys.sql` — schema.
- `supabase/migrations/0024_api_usage_logs.sql` — cost tracking.
- `supabase/migrations/0025_admin_alerts.sql` — alerts.
- `apps/api/services/key_resolver.py` — wrapper.
- `apps/api/services/vault.py` — encryption helper (AES-GCM thay vì Vault).
- `apps/api/routers/admin_api_keys.py` — 7 endpoints.
- `apps/api/routers/admin_alerts.py` — 2 endpoints.
- `apps/web/app/api/admin/api-keys/route.ts` — web proxy.
- `apps/web/app/api/admin/api-keys/[id]/route.ts` — web proxy.
- `apps/web/app/api/admin/api-keys/[id]/test/route.ts` — web proxy.
- `apps/web/app/api/admin/api-keys/[id]/rotate/route.ts` — web proxy.
- `apps/web/app/api/admin/alerts/route.ts` — web proxy.
- `apps/web/app/(admin)/admin/api-keys/page.tsx` — UI.
- `apps/web/app/(admin)/admin/alerts/page.tsx` — UI.

### Quyết định Encryption — đơn giản hóa
- **Plan gốc** dùng Supabase Vault (managed). Nhưng Vault extension cần enable riêng trên Supabase instance.
- **Phase 7 dùng AES-GCM encryption** (`cryptography.Fernet`) với key từ env `ENCRYPTION_KEY`:
  - Lưu `encrypted_value` vào `api_provider_keys` (BYTES, không ai đọc được raw value).
  - Decrypt chỉ khi cần gọi provider (admin test endpoint).
  - `key_resolver` cache plaintext 60s trong memory.
  - Mask trong audit log: `audit._SENSITIVE_KEYS` đã có pattern.

## 3. Các File liên quan và Vai trò

### Migrations (3 NEW)
- `supabase/migrations/0023_api_provider_keys.sql` — `api_provider_keys` table + indexes.
- `supabase/migrations/0024_api_usage_logs.sql` — `api_usage_logs` table + trigger UPDATE cost.
- `supabase/migrations/0025_admin_alerts.sql` — `admin_alerts` table + RPC `create_alert`.

### Backend services (2 NEW)
- `apps/api/services/vault.py` — `encrypt(plain) → bytes`, `decrypt(cipher) → plain` dùng Fernet.
- `apps/api/services/key_resolver.py` — `resolve_key(provider) → str` cache 60s + fallback chain từ DB.

### Backend routers (2 NEW)
- `apps/api/routers/admin_api_keys.py` — 7 endpoints (list, create, update, rotate, delete, test, usage).
- `apps/api/routers/admin_alerts.py` — 2 endpoints (list unresolved, resolve).

### Backend integration (1 NEW)
- `apps/api/services/usage_tracker.py` — decorator `@track_usage(provider)` log + cost increment.

### Frontend (7 NEW)
- 5 web proxy routes (api-keys list/create + detail/update + test + rotate + alerts list/resolve).
- 2 trang admin (`/admin/api-keys` + `/admin/alerts`).

### Frontend (1 UPDATE)
- `apps/web/app/(admin)/layout.tsx` — enable `API Keys` + `Alerts` sidebar (line 12, 14).

### Files KHÔNG đụng
- Phase 5 files (`require_admin`, `audit.py`, migration 0022).
- Phase 6 files (sẽ có sau khi Tier 2 thực thi Phase 6).
- User-facing routes.
- Worker tasks (chưa refactor `key_resolver` cho worker Phase 7 — để Phase 8+).

## 4. Dependencies
- **External:** `cryptography` (Fernet) — đã có sẵn trong Python 3.7+ stdlib không, **CẦN cài** (`pip install cryptography`).
- **Internal:** `apps.api.dependencies.admin.require_admin`, `apps.api.services.audit.log_admin_action`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Encryption key:** PHẢI set `ENCRYPTION_KEY` trong `.env` (Fernet key 44-char base64). Phase 7 tạo script generate key.
- **Không đụng Phase 5 + Phase 6 files.**
- **Audit mask:** Đã có ở Phase 5. KHÔNG log raw key value ra audit.
- **Cost tracking:** Phase 7 chỉ implement DECORATOR + DB schema. Cron reset cost đầu tháng Phase 9+.
- **Worker refactor:** Phase 7 KHÔNG refactor worker (giữ nguyên `os.environ`). Phase 8+ sẽ dùng `key_resolver`.

## 6. Output mong đợi

Sau Phase 7:
- Admin click `/admin/api-keys` → thấy table providers (OpenAI, Cohere, R2, Modal, ...) với active key count + monthly cost.
- Click "Add Key" → form (provider, label, value) → encrypt + insert vào DB.
- Click "Test" → ping provider → return `{ok: bool, latency_ms, error}`.
- Click "Rotate" → form new value → archive old + insert new (old value giữ 7 ngày trong DB).
- `/admin/alerts` → list unresolved budget alerts + Resolve button.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- 3 migration mới áp dụng thành công (không break schema cũ).
- `key_resolver` + `vault` services import OK.
- 9 endpoint admin (7 api-keys + 2 alerts) + mount vào `main.py`.
- 5 web proxy + 2 trang admin UI + sidebar update.
- Test key rotation KHÔNG break TTS route (vẫn dùng `os.environ` cho đến Phase 8+).
- TS compile 0 errors.