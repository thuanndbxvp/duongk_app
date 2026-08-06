# Bối cảnh Hệ thống (CONTEXT): phase9-admin-polish

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A5)
- **Phase 5 đã xong:** `require_admin` + `audit.py:log_admin_action` + migration 0022.
- **Phase 6/7/8 đã viết plan** (chưa thực thi): User/Credit, API Keys (Fernet), Service Routing (Redis pub/sub).
- **Đây là Sprint A5 — phase cuối cùng của admin panel:** Polish + Extended features.

## 2. Codebase Analysis (qua Read + Grep)

### Discovery — Phase 5/6/7/8 đã chuẩn bị
- **`apps/api/dependencies/admin.py:15`** — `require_admin` dependency (cache 60s).
- **`apps/api/services/audit.py:27`** — `log_admin_action()` + `_mask_value()` (đã có).
- **`supabase/migrations/0022_admin_panel_foundation.sql`** — có `admin_audit_logs` table (RLS deny non-service).
- **`apps/web/app/(admin)/layout.tsx`** — sidebar có `Audit Logs.enabled = false` (chưa enable).
- **Migration tới 0026** (Phase 8 seed 8 routing features).

### Hiện trạng Phase 9 cần thêm (qua Grep)
- ❌ **KHÔNG CÓ** `admin_audit_logs` viewer UI (`/admin/audit-logs`).
- ❌ **KHÔNG CÓ** MFA / TOTP integration.
- ❌ **KHÔNG CÓ** IP whitelist middleware (`ADMIN_ALLOWED_IPS`).
- ❌ **KHÔNG CÓ** backup/restore config script.
- ❌ **KHÔNG CÓ** admin handbook (`docs/admin_handbook.md`).
- ❌ **KHÔNG CÓ** `apps/worker/services/render_dispatcher.py` (ffmpeg).
- ❌ **KHÔNG CÓ** thumbnail_vision consumer (chưa có module).

### Admin panel feature checklist (admin_panel_plan.md mục 2.7)
Sprint A5 cần 6 features:
1. **Audit log viewer UI** với full-text search + JSON diff viewer.
2. **Advanced dashboard analytics:** cohort retention, top creators, revenue chart.
3. **Backup/restore config:** dump `service_routing_config` + `credit_pricing` + `api_provider_keys.metadata` → JSON.
4. **Documentation:** `docs/admin_handbook.md`.
5. **2FA bắt buộc cho super_admin** (Supabase MFA TOTP).
6. **IP whitelist enforcement** (Caddy + FastAPI).

### Sprint A5 plan tiết kiệm (đơn giản hóa)
Phase 9 sẽ implement **3 trọng tâm** (tránh over-scope):
1. **Audit log viewer UI** + JSON diff viewer + export CSV.
2. **IP whitelist enforcement** (FastAPI middleware).
3. **Documentation** (`docs/admin_handbook.md`).

3 features còn lại (MFA TOTP, advanced analytics, backup/restore script, ffmpeg dispatcher, thumbnail_vision) → Phase 10+ sau khi admin panel MVP xong.

### Consumer refactor tận dụng Phase 8
- Phase 8 đã có `select_llm_provider()`, `select_emotion_provider()`, `_select_embedding_provider()`. Phase 9 chỉ **wire** chúng vào method chính (chứ chưa wire Phase 8).
- Phase 9 chỉnh sửa 2-3 method nhỏ để thật sự dùng `routing.get_routing_config()` thay hardcode (Phase 8 stub).

## 3. Các File liên quan và Vai trò

### Backend services (2 NEW)
- `apps/api/services/ip_whitelist.py` — FastAPI middleware check IP từ env `ADMIN_ALLOWED_IPS`.
- `apps/api/services/backup.py` — helper dump/restore config (3 tables: `service_routing_config`, `credit_pricing`, `api_provider_keys.metadata`).

### Backend routers (1 NEW)
- `apps/api/routers/admin_audit.py` — 3 endpoints (list với full-text search, get detail, export CSV).

### Backend integration (1 NEW)
- `apps/api/middleware/__init__.py` — register IP whitelist middleware cho `/api/admin/**`.

### Frontend (4 NEW + 1 UPDATE)
- 1 web proxy: `apps/web/app/api/admin/audit-logs/route.ts` (GET list) + detail.
- 1 trang admin: `apps/web/app/(admin)/admin/audit-logs/page.tsx` (table + filter + JSON diff modal).
- Sidebar enable Audit Logs (line 15).

### Docs (1 NEW)
- `docs/admin_handbook.md` — hướng dẫn sử dụng admin panel cho admin mới.

### Consumer wire (2 UPDATE — Phase 8 stub → fully wired)
- `apps/api/modules/rag/embedder.py` — wire `_select_embedding_provider()` vào `embed_texts()`.
- `apps/worker/tasks/script_generate.py` — wire `select_llm_provider()` vào `generate_script()`.

### Files KHÔNG đụng
- Phase 5/6/7/8 files (admin routers, audit, key_resolver, vault, routing).
- User-facing routes.
- Worker task files KHÔNG thuộc wire (analysis_task, idea_generate, etc.).

## 4. Dependencies
- **External:** `ipaddress` (stdlib) cho IP whitelist.
- **Internal:** `apps.api.dependencies.admin.require_admin`, `apps.api.services.audit.log_admin_action`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **MFA Phase 9 chỉ document** — Supabase MFA TOTP setup ở Phase 10+ (vì cần enable MFA trên Supabase project).
- **IP whitelist:** Cấu hình qua env `ADMIN_ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8`. Empty = allow all (dev mode).
- **Audit log viewer:** Read-only, không có delete.
- **Documentation:** Tiếng Việt + English (song ngữ).

## 6. Output mong đợi

Sau Phase 9:
- Admin click `/admin/audit-logs` → thấy table audit log với filter (admin_email, action, target_type, target_id, date range) + pagination.
- Click row → modal hiển thị JSON diff `before` vs `after`.
- Click "Export CSV" → download file audit log.
- IP whitelist middleware block request từ IP không thuộc `ADMIN_ALLOWED_IPS` (trong dev = allow all).
- 2 file consumer (`embedder`, `script_generate`) thật sự dùng routing config (không phải stub).
- `docs/admin_handbook.md` có hướng dẫn onboarding cho admin mới.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- 2 service mới (`ip_whitelist`, `backup`).
- 1 router admin (3 endpoint audit log viewer).
- 1 middleware IP whitelist registered trong main.py.
- 2 consumer wire (`embedder`, `script_generate`).
- 4 file frontend (1 proxy + 1 page + 1 export button + sidebar update).
- 1 file docs (`docs/admin_handbook.md`).
- TS compile 0 errors.
- Existing pytest PASSED.
- IP whitelist test: request từ IP không match → 403.
- Audit log viewer test: filter + JSON diff + export CSV hoạt động.