# Bối cảnh Hệ thống (CONTEXT): phase5-audit-fixes-foundation

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md`
- **CodeGraph status:** indexed (đã query thành công qua MCP `user-codegraph`)

## 2. Codebase Analysis (via CodeGraph MCP — `codegraph_context` với task: FastAPI router + credit_manager + migration 0020)

### Discovery
- Có 40 routes được mount trong FastAPI app. URL manifest đã được codegraph xác nhận.
- `apps/api/services/credit_manager.py:hold()` gọi RPC `hold_credits(p_user_id, p_amount, p_job_id)` — signature **mới** (đảo tham số so với 0006).
- `apps/api/test_credit_manager.py` đã có 2 unit test pass cho `hold_succeeds` và `hold_insufficient_raises`.
- `apps/api/routers/projects.py:start_project` dùng `CreditManager.hold(...)` (line 60) — entry point duy nhất hiện tại gọi hold.

### Related Symbols (đã xác nhận)
- `CreditManager` class at `apps/api/services/credit_manager.py:20`
- `hold` method at `apps/api/services/credit_manager.py:41` — signature `(self, user_id: str, job_id: str, amount: int) -> dict`
- `start_project` at `apps/api/routers/projects.py:19`
- `test_hold_succeeds` at `apps/api/test_credit_manager.py:27`
- `test_hold_insufficient_raises` at `apps/api/test_credit_manager.py:34`

### Callers Analysis
- `hold()` callers: **1** (chỉ `start_project`)
- `start_project` callers: HTTP route `/api/projects/start`

### Callees Analysis
- `hold()` calls:
  - `self.admin.rpc('hold_credits', {...})` — Supabase RPC
- `start_project()` calls:
  - `CreditManager().hold(...)`
  - `get_supabase_admin().table(...)` (channel_assistants.insert, jobs.insert, jobs.update)
  - `analyze_channel_task.delay(...)` (Celery dispatch)
  - `re.search(...)`

## 3. Các File liên quan và Vai trò

### Backend (apps/api)
- `apps/api/main.py:1` — App FastAPI + router registration. Mount 12 routers từ `apps/api/routers/*` và `apps/api/modules/*`.
- `apps/api/routers/projects.py:1` — `/api/projects/start` endpoint. Là route duy nhất hiện gọi `cm.hold`. **Phase này không đụng route này** (nó hoạt động).
- `apps/api/routers/users.py:1` — `/users/me` CRUD. **Đã OK.**
- `apps/api/routers/credits.py:1` — `/credits/balance`, `/credits/transactions`. **Đã OK.**
- `apps/api/services/credit_manager.py:1` — `CreditManager` class + PRICING dict. **Cần thêm wrapper `get_user_role()` nếu dùng cho admin RBAC**, nhưng KHÔNG đụng trong phase này.

### Web (apps/web)
- `apps/web/middleware.ts` — **chưa tồn tại**. Phase này sẽ tạo mới để check role cho `/admin/**`.
- `apps/web/app/(admin)/` — **chưa tồn tại**. Phase này tạo route group + layout shell.
- `apps/web/lib/auth.ts` — có sẵn `getAccessToken()`, `getFullUser()` — sẽ dùng cho admin middleware.

### Migrations (supabase/migrations/)
- `0001_users.sql` — tạo `users(id, email, credits, tier, created_at, updated_at)`. **Cần ALTER TABLE thêm `role`, `max_assistants`, `banned_at`, `banned_reason`, `deleted_at`, `last_sign_in_at`.**
- `0006_credit_hold_commit.sql` — định nghĩa `hold_credits(p_user_id, p_job_id, p_amount)` — **duplicate signature với 0020**.
- `0020_credit_tiers.sql` — định nghĩa `hold_credits(p_user_id, p_amount, p_job_id)` (mới) + `credit_pricing` table + `admin_adjust_credits` (chưa có, cần thêm).
- `0011_transcripts_cron.sql` — `transcripts` table + RLS policy "Authenticated users can view transcripts" — **leaky**.

## 4. Dependencies
- **External:** fastapi, supabase-py, python-jose (jwt), celery, redis
- **Internal:** `apps.api.dependencies.auth.get_supabase_user`, `apps.api.dependencies.supabase.get_supabase_admin`

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7). Tất cả verify command dùng `Invoke-RestMethod`, `pytest`, `pnpm dev`.
- **Line Ending:** CRLF. Tier 2 KHÔNG dùng `Write` tạo file từ đầu mà dùng `StrReplace` để giữ CRLF.
- **Migration order:** Tất cả migrations chạy theo tên file tăng dần (Supabase CLI `supabase db push`). Migration mới phải có timestamp/seq > `0021_voice_profiles.sql`.
- **Backward compatibility:** Khi thêm column `role` vào `users`, **PHẢI** có default `'user'` để không break 100% dữ liệu hiện tại.
- **BẢO TỒN:** Tất cả code đang chạy production (TTS, credit hold, Supabase Auth) **không được đụng**.
- **Không có frontend framework sẵn cho admin**: phase này tạo minimum shell, không cần shadcn/ui — dùng Tailwind glass system hiện có.

## 6. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- Migrations áp dụng thành công, không break API hiện tại.
- FastAPI `/api/research/validate` (existing) vẫn return 200.
- `/admin` route redirect đúng khi không login.
- Không có regression nào trên `credit_manager` unit test.
