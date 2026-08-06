# Plan: Admin Panel (CPanel) — AppDK
> Ngày: 2026-08-06 · Tác giả: Cursor Assistant · Phạm vi: Phần 2 trong `docs/Plan_Cpanel.md`
> Dựa trên: Codebase audit đã thực hiện tại `docs/audit/codebase_audit_report.md`

---

## Tóm tắt quyết định (đã xác nhận với user)
| Quyết định | Lựa chọn |
|-----------|----------|
| Triển khai | Route `/admin/*` trong app Next.js chính (không tách `apps/admin`) |
| RBAC | Thêm column `role` vào `users` (không tạo bảng `admin_users` riêng) |
| Encryption API key | **Supabase Vault** (managed) |
| Phạm vi file này | **Phase 1: chỉ viết plan**, không scaffold code |

---

## 2.1 Phạm vi tính năng (MVP)

### A. Quản trị User
- **List user**: bảng với search theo email/name, filter theo `tier` (free/pro/enterprise), `status` (active/banned), `created_at` range. Pagination 50/trang.
- **User detail**: tab "Profile" (full_name, avatar, email, tier, role, created_at, last_sign_in_at), tab "Credits" (balance + ledger view inline), tab "Jobs" (recent 50 jobs với status), tab "Projects" (count assistants + count scripts).
- **Create user thủ công**: dành cho invite/comp account → tạo row trong `auth.users` + `public.users` đồng thời, set `credits` ban đầu (configurable), gửi invite email qua Supabase.
- **Edit user**: đổi `tier`, `email` (cập nhật cả `auth.users`), `max_assistants` (cột mới — xem 2.3), `role`. Tất cả thay đổi phải audit-log.
- **Soft delete**: cột `deleted_at TIMESTAMPTZ`, mọi query ở app chính phải filter `deleted_at IS NULL`. Recovery window **7 ngày** (cron job xoá cứng sau đó).
- **Ban/unban**: cột `banned_at`, khi banned: set `auth.users.banned_until` (Supabase Auth) + cờ `is_disabled` ở app. Lý do ban bắt buộc (lưu `admin_audit_logs`).
- **Impersonate**: tạo short-lived JWT (TTL 15 phút) gắn cờ `impersonated_by = admin_id`. Mọi hành động trong session impersonate đều log với `impersonated_by` rõ ràng.

### B. Quản trị Credit
- **Adjust credit**: form `{user_id, delta, reason (bắt buộc ≥ 10 ký tự)}` → gọi RPC `admin_adjust_credits(p_user_id, p_delta, p_admin_id, p_reason)`. Tự động tạo row `credit_transactions` với action=`admin_adjust`.
- **Credit ledger toàn hệ thống**: bảng phân trang theo `created_at`, filter theo `user_id`, `action`, `amount range`. Có toggle "group by user" hiển thị tổng net per user.
- **Per-user transaction history**: drill-down từ user detail.
- **Stats panel**:
  - `total_credits_issued` (tổng `amount > 0` tất cả tx)
  - `total_credits_spent` (tổng `amount < 0` với action != `refund`)
  - `total_credits_hold` (sum `jobs.credits_held WHERE status='running'`)
  - `total_credits_refunded` (tổng `amount > 0` với action = `refund`)
  - Card riêng cho từng metric + sparkline 30 ngày.
- **Export CSV**: chọn date range, output 6 cột: `tx_id, user_email, action, amount, balance_after, reason, created_at`. Stream lớn qua `text/csv`.
- **Pricing config UI**: CRUD bảng `credit_pricing` (đã tồn tại ở `0020_credit_tiers.sql`) — UI cho phép sửa `credits` per `job_type` + cờ `enabled`. Hot-reload qua Redis pub/sub (xem 2.4).

### C. Quản trị API Key của AI providers
- **CRUD providers**: OpenAI · Gemini · Cohere · ElevenLabs · YouTube Data API (multi-key rotation) · Pexels · Pixabay · Unsplash · Modal · Supabase service role · R2 credentials.
- Mỗi key có: `provider`, `label` (vd "OpenAI key #1"), `encrypted_value` (Supabase Vault), `version`, `is_active`, `rate_limit_rpm`, `monthly_budget_usd`, `last_used_at`, `expires_at`.
- **Rotate an toàn**: thêm key mới (`is_active=true`) trước, đánh dấu key cũ `is_active=false` nhưng vẫn giữ value để fallback. Worker load key theo `created_at DESC` trong nhóm active.
- **Test connectivity**: POST `/api/admin/api-keys/{id}/test` → tự gọi 1 request nhỏ đến provider tương ứng (vd OpenAI → `models.list()`). Trả về `{ok: bool, latency_ms, error}`.
- **Usage/cost monitor**: query `api_usage_logs` group by `provider_key_id` 24h/7d/30d. Card hiển thị: requests, success_rate, avg_latency, est_cost.
- **Alert**: cron job (Supabase scheduled function) mỗi giờ check `current_month_cost > 80% monthly_budget` → insert vào `admin_alerts` + (optional) email qua Resend.

### D. Cấu trúc Routing Service (tính năng cốt lõi)
- Mỗi **nghiệp vụ** (xem danh sách dưới) có 1 routing rule gồm: **primary provider** + **fallback chain** (ordered list) + **enabled flags** per provider + **cost estimate per call**.
- Lưu trong bảng `service_routing_config` (xem 2.3). Worker **hot-reload** bằng cách subscribe Redis channel `routing:config:update` (publish khi admin save UI). Fallback nếu Redis down: worker polling DB mỗi 60s.
- **8 nghiệp vụ cần routing**:
  1. `transcript_extract` → Supadata | Youtube-Transcript.io | youtube-transcript-api (local CPU) | Modal Whisper (GPU)
  2. `llm_text` (script gen, mimic rules) → OpenAI GPT-4o | Anthropic Claude | Stali | Modal self-hosted
  3. `embedding` (chia theo lang) → Cohere multilingual (vi) | OpenAI text-embedding-3 (en)
  4. `emotion_classifier` → OpenAI GPT-4o-mini | Anthropic Claude Haiku
  5. `ffmpeg_render` → Modal GPU T4 | Modal GPU A10G | Local CPU VPS (slow fallback)
  6. `tts` → Modal OmniVoice | ElevenLabs | OpenAI TTS
  7. `thumbnail_vision` → OpenAI GPT-4o | Gemini Vision
  8. `footage_search` → Pexels | Pixabay | Unsplash (priority weighted random)
- **Cost estimate preview**: UI hiển thị "nếu chọn provider X với fallback Y → ước tính $X.XX / 1000 calls" dựa trên `cost_per_call_usd` cache từ `api_usage_logs` lịch sử.

---

## 2.2 Kiến trúc kỹ thuật Admin Panel

### Triển khai: Route `/admin` trong `apps/web` (đã chọn)
- Lý do: tận dụng design system (glass + gradient), Supabase session, middleware đã có. Không cần infra mới.
- Layout: `apps/web/app/(admin)/layout.tsx` riêng, không dùng `AuthenticatedLayout` của dashboard — dùng `AdminShell` với sidebar riêng.
- Auth guard: `middleware.ts` ở root, check role cho mọi route `/admin/**` (xem bên dưới).
- **Phân tách bundle**: lazy import các trang admin (`dynamic()`) để không ảnh hưởng LCP của user-facing app.

### Auth & RBAC
- **Supabase Auth dùng chung**. Thêm column `role` vào `public.users` (`'user' | 'admin' | 'super_admin'`).
- **Middleware** `apps/web/middleware.ts`:
  ```ts
  // pseudo-code
  if (pathname.startsWith('/admin')) {
    const { data: user } = await supabase.auth.getUser();
    if (!user) redirect('/login');
    const role = await getUserRole(user.id);  // cached 60s
    if (!['admin', 'super_admin'].includes(role)) redirect('/403');
  }
  ```
- FastAPI side: thêm dependency `apps/api/dependencies/admin.py`:
  ```python
  def require_admin(user_id = Depends(get_supabase_user)) -> str:
      role = get_user_role(user_id)
      if role not in ('admin', 'super_admin'):
          raise HTTPException(403, 'Admin only')
      return user_id
  ```
  Decorator `@require_admin` wrap mọi route `/api/admin/*`.

### 2FA (optional MVP)
- MVP: chỉ yêu cầu password + role check.
- Phase 2: bật TOTP qua Supabase MFA (`factor_type='totp'`), bắt buộc với `super_admin`.

### Realtime
- Bảng `admin_audit_logs` + `jobs` + `credit_transactions` enable Supabase Realtime. Admin dashboard subscribe để cập nhật stats real-time.
- Bảng `service_routing_config` không cần realtime — dùng Redis pub/sub để notify worker (admin save → server publish → worker reload).

### Audit log
- Mọi mutation endpoint admin gọi 1 helper `apps/api/services/audit.py:log_admin_action(admin_id, action, target_type, target_id, before, after, ip, user_agent)`.
- Helper này INSERT vào `admin_audit_logs` (xem 2.3).
- Trước khi write, mask tất cả field có tên `*key*`, `*token*`, `*secret*`, `*password*` → thay bằng `***`.

---

## 2.3 Database Schema cần thêm

> Tất cả migration đặt vào `supabase/migrations/0022_admin_panel.sql` (đánh số tiếp theo file mới nhất hiện tại `0021_voice_profiles.sql`).

```sql
-- ============================================================
-- Migration: 0022_admin_panel.sql
-- Purpose: Admin panel foundation (RBAC, audit, routing, encrypted API keys, dynamic pricing)
-- ============================================================

-- 1) Add role + max_assistants to users (backward compatible)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
    CHECK (role IN ('user', 'admin', 'super_admin')),
  ADD COLUMN IF NOT EXISTS max_assistants INT NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS banned_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS banned_reason TEXT,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_sign_in_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier) WHERE deleted_at IS NULL;

-- 2) Admin audit log
CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID NOT NULL REFERENCES users(id),
  admin_email TEXT NOT NULL,  -- denormalized for display
  action TEXT NOT NULL,        -- 'user.update', 'credit.adjust', 'api_key.create', 'routing.update', etc.
  target_type TEXT NOT NULL,   -- 'user', 'credit', 'api_key', 'routing', 'pricing'
  target_id TEXT,              -- UUID or composite key as text
  before JSONB,                -- snapshot before change (sanitized)
  after JSONB,                 -- snapshot after change (sanitized)
  ip INET,
  user_agent TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_admin ON admin_audit_logs(admin_id, created_at DESC);
CREATE INDEX idx_audit_target ON admin_audit_logs(target_type, target_id, created_at DESC);
CREATE INDEX idx_audit_action ON admin_audit_logs(action, created_at DESC);

-- RLS: only service_role reads/writes (admin uses service_role on backend)
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
-- No explicit policy needed for non-service roles → default deny

-- 3) Service routing config
CREATE TABLE IF NOT EXISTS service_routing_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feature TEXT NOT NULL UNIQUE,        -- 'transcript_extract', 'llm_text', 'embedding', ...
  primary_provider TEXT NOT NULL,      -- 'openai', 'modal', 'supadata', etc.
  fallback_chain TEXT[] NOT NULL DEFAULT '{}',  -- ordered array
  enabled_providers JSONB NOT NULL DEFAULT '{}',  -- {provider: bool}
  cost_per_call_usd JSONB NOT NULL DEFAULT '{}',  -- {provider: number}
  config_version INT NOT NULL DEFAULT 1,
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_routing_feature ON service_routing_config(feature);

-- Seed default routing for 8 features
INSERT INTO service_routing_config (feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd) VALUES
  ('transcript_extract', 'supadata', ARRAY['youtube_transcript_api','modal_whisper'], '{"supadata":true,"youtube_transcript_api":true,"modal_whisper":true}', '{"supadata":0.001,"youtube_transcript_api":0,"modal_whisper":0.006}'),
  ('llm_text', 'openai', ARRAY['stali'], '{"openai":true,"stali":true,"anthropic":false}', '{"openai":0.005,"stali":0.002,"anthropic":0.008}'),
  ('embedding', 'cohere', ARRAY['openai'], '{"cohere":true,"openai":true}', '{"cohere":0.0001,"openai":0.00013}'),
  ('emotion_classifier', 'openai', ARRAY[]::TEXT[], '{"openai":true}', '{"openai":0.0005}'),
  ('ffmpeg_render', 'modal_t4', ARRAY['modal_a10g','local_cpu'], '{"modal_t4":true,"modal_a10g":true,"local_cpu":true}', '{"modal_t4":0.02,"modal_a10g":0.04,"local_cpu":0.0}'),
  ('tts', 'modal_omnivoice', ARRAY['elevenlabs','openai_tts'], '{"modal_omnivoice":true,"elevenlabs":true,"openai_tts":true}', '{"modal_omnivoice":0.008,"elevenlabs":0.018,"openai_tts":0.015}'),
  ('thumbnail_vision', 'openai', ARRAY['gemini'], '{"openai":true,"gemini":false}', '{"openai":0.0075,"gemini":0.0025}'),
  ('footage_search', 'pexels', ARRAY['pixabay','unsplash'], '{"pexels":true,"pixabay":true,"unsplash":true}', '{"pexels":0,"pixabay":0,"unsplash":0}')
ON CONFLICT (feature) DO NOTHING;

-- 4) API provider keys (encrypted via Supabase Vault)
CREATE TABLE IF NOT EXISTS api_provider_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,               -- 'openai', 'gemini', 'cohere', 'elevenlabs', 'youtube', 'pexels', 'pixabay', 'unsplash', 'modal', 'supabase_service_role', 'r2'
  label TEXT NOT NULL,                  -- 'OpenAI key #1'
  secret_id UUID NOT NULL,              -- FK to vault.secrets (Supabase Vault)
  is_active BOOLEAN NOT NULL DEFAULT true,
  rate_limit_rpm INT,
  monthly_budget_usd NUMERIC(10,2),
  current_month_cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  last_tested_at TIMESTAMPTZ,
  last_test_status TEXT,                -- 'ok' | 'fail' | 'timeout'
  expires_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(provider, label)
);
CREATE INDEX idx_apikeys_provider ON api_provider_keys(provider) WHERE is_active;

-- 5) Dynamic pricing config (override credit_pricing defaults)
-- We reuse the existing `credit_pricing` table from 0020 but add 'enabled' flag
ALTER TABLE credit_pricing
  ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- 6) Admin alerts (for budget/quota alerts)
CREATE TABLE IF NOT EXISTS admin_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
  category TEXT NOT NULL,                -- 'budget', 'quota', 'error_rate', 'security'
  message TEXT NOT NULL,
  context JSONB DEFAULT '{}',
  resolved_at TIMESTAMPTZ,
  resolved_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_unresolved ON admin_alerts(created_at DESC) WHERE resolved_at IS NULL;

-- 7) RPC: admin adjust credits (atomic + audit)
CREATE OR REPLACE FUNCTION admin_adjust_credits(
  p_admin_id UUID,
  p_user_id UUID,
  p_delta INT,
  p_reason TEXT
) RETURNS TABLE(new_balance INT, tx_id UUID) AS $$
DECLARE
  v_current INT;
  v_tx_id UUID;
BEGIN
  IF p_reason IS NULL OR length(trim(p_reason)) < 10 THEN
    RAISE EXCEPTION 'Reason required (min 10 chars)';
  END IF;

  SELECT credits INTO v_current FROM users WHERE id = p_user_id FOR UPDATE;
  IF v_current IS NULL THEN RAISE EXCEPTION 'User not found'; END IF;

  UPDATE users SET credits = credits + p_delta, updated_at = NOW() WHERE id = p_user_id;

  INSERT INTO credit_transactions (user_id, action, amount, balance_after, reason, metadata)
  VALUES (p_user_id, 'admin_adjust', p_delta, v_current + p_delta, p_reason,
          jsonb_build_object('admin_id', p_admin_id))
  RETURNING id INTO v_tx_id;

  RETURN QUERY SELECT v_current + p_delta, v_tx_id;
END;
$$ LANGUAGE plpgsql;

-- 8) Soft-delete helper
CREATE OR REPLACE FUNCTION soft_delete_user(p_user_id UUID) RETURNS void AS $$
BEGIN
  UPDATE users SET deleted_at = NOW() WHERE id = p_user_id;
  -- Future: anonymize PII in auth.users
END;
$$ LANGUAGE plpgsql;
```

### Notes kỹ thuật
- **Supabase Vault**: dùng extension `vault` (đã có sẵn trên Supabase managed). Lệnh `vault.create_secret(secret_value, name)`. Lưu ý: `secret_id` trong `api_provider_keys` reference tới `vault.secrets.id` — cần thêm FK literal (Supabase không expose rõ FK). Tạm thời chỉ lưu UUID dạng TEXT + check existence ở app layer.
- **Cost tracking**: trigger AFTER INSERT trên `api_usage_logs` (nếu chưa có) để tự cộng dồn vào `current_month_cost_usd`. Cron job reset về 0 đầu tháng.
- **Routing hot-reload**: thêm Postgres trigger `AFTER UPDATE ON service_routing_config` → gọi `pg_notify('routing:config:update', NEW.feature)`. Worker `LISTEN` channel này qua `psycopg2` connection riêng (xem 2.7 Sprint A4).

---

## 2.4 API Endpoints cho Admin

> Tất cả routes mount dưới prefix `/api/admin`. Tất cả đều `@require_admin` (xem 2.2). Service_role key dùng để bypass RLS cho mọi thao tác admin.

### User Management
| Method | Path | Mục đích | Body / Response |
|--------|------|----------|-----------------|
| GET | `/api/admin/users` | List + filter + paginate | Query: `q`, `tier`, `status`, `role`, `from`, `to`, `page`, `limit` → `{users: [...], total}` |
| GET | `/api/admin/users/:id` | Chi tiết 1 user (profile + counts) | → UserDetail |
| POST | `/api/admin/users` | Tạo user mới (invite) | `{email, full_name, tier, credits, max_assistants}` → User |
| PATCH | `/api/admin/users/:id` | Cập nhật user | `{tier?, email?, max_assistants?, role?, full_name?}` |
| DELETE | `/api/admin/users/:id` | Soft delete | `{reason}` → 204 |
| POST | `/api/admin/users/:id/restore` | Khôi phục từ soft-delete (trong 7 ngày) | → User |
| POST | `/api/admin/users/:id/ban` | Ban | `{reason, until?}` |
| POST | `/api/admin/users/:id/unban` | Unban | → User |
| POST | `/api/admin/users/:id/impersonate` | Phát JWT ngắn hạn | `{ttl_minutes=15}` → `{token, expires_at}` |

### Credit Management
| Method | Path | Mục đích |
|--------|------|----------|
| POST | `/api/admin/users/:id/adjust-credit` | `{delta, reason}` → `{new_balance, tx_id}` |
| GET | `/api/admin/credit/ledger` | Query: `user_id?`, `action?`, `from?`, `to?`, `page` → `{transactions, total}` |
| GET | `/api/admin/credit/stats` | → `{total_issued, total_spent, total_hold, total_refunded, sparkline: [...]}` |
| GET | `/api/admin/credit/export` | Query: `from`, `to`, `format=csv` → `text/csv` |
| GET | `/api/admin/pricing` | List `credit_pricing` rows |
| PATCH | `/api/admin/pricing/:job_type` | `{credits?, enabled?, description?}` |
| POST | `/api/admin/pricing/reload` | Publish Redis channel để worker reload cache |

### API Keys
| Method | Path | Mục đích |
|--------|------|----------|
| GET | `/api/admin/api-keys` | List (provider, label, is_active, last_tested_at, current_month_cost_usd) — **không trả value** |
| POST | `/api/admin/api-keys` | `{provider, label, value, rate_limit_rpm?, monthly_budget_usd?, expires_at?}` → insert + vault.create_secret |
| PATCH | `/api/admin/api-keys/:id` | Update metadata (không đổi value) |
| POST | `/api/admin/api-keys/:id/rotate` | `{new_value}` — tạo secret mới, archive cũ (giữ value cũ trong vault 7 ngày) |
| DELETE | `/api/admin/api-keys/:id` | Soft archive |
| POST | `/api/admin/api-keys/:id/test` | Test connectivity |
| GET | `/api/admin/api-keys/:id/usage` | Usage 24h/7d/30d |
| GET | `/api/admin/alerts` | List unresolved alerts |
| POST | `/api/admin/alerts/:id/resolve` | Resolve |

### Service Routing
| Method | Path | Mục đích |
|--------|------|----------|
| GET | `/api/admin/routing-config` | List 8 features với primary + fallback chain |
| GET | `/api/admin/routing-config/:feature` | Chi tiết |
| PATCH | `/api/admin/routing-config/:feature` | `{primary_provider?, fallback_chain?, enabled_providers?, cost_per_call_usd?}` |
| POST | `/api/admin/routing-config/:feature/reload` | Publish Redis `routing:config:update` |

### Dashboard & Audit
| Method | Path | Mục đích |
|--------|------|----------|
| GET | `/api/admin/dashboard/stats` | Top stats: MRR (estimate), active_users_24h, jobs_today, credits_spent_today, errors_top10 |
| GET | `/api/admin/dashboard/traffic` | Sparkline traffic 7 ngày (jobs/credit_tx/api_call) |
| GET | `/api/admin/audit-logs` | Query: `admin_id?`, `action?`, `target_type?`, `target_id?`, `from?`, `to?`, `page` |
| GET | `/api/admin/audit-logs/:id` | Chi tiết (xem `before` / `after` đã masked) |

---

## 2.5 Security Requirements

### Network
- **IP whitelist**: env `ADMIN_ALLOWED_IPS` (comma-separated CIDR). Middleware FastAPI check `request.client.host` ∈ whitelist trước khi vào router.
- Caddy (production) có thể add thêm rule giới hạn path `/admin/*` và `/api/admin/*` theo IP — defense in depth.

### Auth
- Tất cả endpoint `/api/admin/**` yêu cầu JWT + `role IN ('admin', 'super_admin')`.
- Middleware Next.js check tương tự cho mọi route `/admin/**` (UI).
- Session timeout: 30 phút (Supabase JWT TTL config). Re-login required sau đó.

### Audit
- Helper `apps/api/services/audit.py:log_admin_action()` chạy **đồng bộ** trước khi return response. Nếu audit fail → raise 500 (không commit action).
- Fields tự động mask: regex `/(key|token|secret|password|api_key|apiKey)/i` → thay value bằng `"***"` trong `before`/`after`.

### Encryption
- **Supabase Vault**: tất cả API keys lưu qua `vault.create_secret()`. App không bao giờ đọc raw value trừ khi cần gọi provider → server-side worker gọi RPC `vault.read_secret(id)`, cache trong memory 60s.
- `vault.secrets` table đã có RLS mặc định deny → chỉ service_role mới read được.

### Rate limit
- Áp dụng FastAPI middleware hoặc Redis token bucket riêng: 60 requests / phút / admin_id cho `/api/admin/**`. Excess → 429.

### Logging
- Không log raw API key value ra console/Sentry. Custom log filter strip các field `value`, `secret`, `api_key` trước khi ghi log.
- Sentry: thêm `before_send` hook mask các payload chứa keyword `vault`.

---

## 2.6 UI/UX Guidelines

### Stack
- **Tailwind + shadcn/ui** (đồng nhất với app chính nhưng không bắt buộc). Vì app chính đang dùng glass system riêng, admin dùng lại glass + gradient tokens. Component shadcn/ui cho form/table/dialog.
- **Layout**: `apps/web/app/(admin)/layout.tsx`
  - Sidebar cố định 240px, các mục: Dashboard, Users, Credits, Pricing, API Keys, Routing, Alerts, Audit Logs, Settings.
  - Top bar: admin email + role badge + impersonate indicator (nếu có) + Sign out.
  - Breadcrumb dynamic từ URL.
- **Dark mode default** (đã là default của hệ thống). Không có light mode toggle cho MVP.

### Dashboard trang chủ (`/admin`)
4 card thống kê hàng đầu:
1. **MRR estimate** = sum(`tier_pricing × user_count`) theo tier
2. **Active users 24h** = distinct `user_id` từ `jobs` trong 24h
3. **Jobs today** = count jobs created today
4. **Credits spent today** = sum `amount < 0` của tx hôm nay

Bên dưới:
- Biểu đồ traffic 7 ngày (recharts hoặc chart.js) — multi-line: jobs, credit_tx, api_calls.
- Bảng "Top errors" từ Sentry (chỉ summary, không drill — phase 2).
- Bảng "Recent admin actions" (5 gần nhất từ audit_logs).

### Các trang khác
- **Users** (`/admin/users`): table với filter bar (search, tier, status, role), pagination. Click row → detail page với tabs.
- **User detail** (`/admin/users/[id]`): tabs Profile | Credits | Jobs | Projects | Audit. Action bar: Adjust Credit, Ban/Unban, Impersonate, Delete.
- **Credits** (`/admin/credits`): ledger table + 4 stat cards + Export CSV button.
- **Pricing** (`/admin/pricing`): table `credit_pricing` với inline edit `credits` & `enabled`. Save → publish Redis reload.
- **API Keys** (`/admin/api-keys`): table theo provider, accordion mở rộng hiển thị list keys + test button.
- **Routing** (`/admin/routing`): 8 cards (mỗi feature 1 card), bên trong dropdown primary + ordered list fallback + toggle enabled per provider + cost preview box.
- **Audit Logs** (`/admin/audit-logs`): table phân trang, filter theo admin/action/target/date. Row expand để xem `before`/`after` JSON.
- **Alerts** (`/admin/alerts`): list unresolved + resolve button.

### Patterns chung
- **Confirm dialog** (shadcn AlertDialog) cho mọi destructive action (delete, ban, force pricing change).
- **Toast** (sonner hoặc shadcn toast) cho mọi mutation — success/error.
- **Loading states**: skeleton loaders, không dùng spinner trống.
- **Form validation**: react-hook-form + zod schemas chia sẻ với backend Pydantic schemas.

---

## 2.7 Roadmap thực thi (5 sprints × 1 tuần)

### Sprint A1 — Foundation (1 tuần)
- [ ] Migration `0022_admin_panel.sql` apply thành công (vault extension đã có sẵn).
- [ ] Thêm column `role`/`max_assistants`/`banned_at`/`deleted_at` vào `users`.
- [ ] FastAPI: `apps/api/dependencies/admin.py:require_admin`.
- [ ] Service `apps/api/services/audit.py:log_admin_action` + masking helper.
- [ ] Service `apps/api/services/vault.py` wrapper `vault.create_secret` / `vault.read_secret`.
- [ ] RPC `admin_adjust_credits` test được qua psql.
- [ ] Next.js middleware check `/admin/**` redirect.
- [ ] Layout `apps/web/app/(admin)/layout.tsx` (AdminShell với sidebar).
- [ ] Dashboard `/admin` với 4 stat cards (dữ liệu hard-coded placeholder).

**Definition of Done**: super_admin đăng nhập thấy `/admin` dashboard trống với 4 card "—".

### Sprint A2 — User & Credit Management (1 tuần)
- [ ] Endpoints `/api/admin/users` (GET, POST, PATCH, DELETE, restore, ban, unban, impersonate).
- [ ] `/api/admin/users/:id` (GET) trả về stats inline.
- [ ] `/api/admin/users/:id/adjust-credit` (POST).
- [ ] `/api/admin/credit/ledger` (GET) + `/api/admin/credit/stats` (GET).
- [ ] `/api/admin/credit/export?format=csv` (GET).
- [ ] UI: `/admin/users` table + filter + pagination.
- [ ] UI: `/admin/users/[id]` tabs + action bar.
- [ ] UI: `/admin/credits` ledger + stats + export button.
- [ ] Soft-delete cron: Supabase scheduled function xoá `deleted_at < NOW() - 7 days`.

**Definition of Done**: admin search được user, adjust credit, ban, impersonate. Mọi mutation xuất hiện trong audit log.

### Sprint A3 — API Key Management (1 tuần)
- [ ] CRUD `/api/admin/api-keys` + test endpoint.
- [ ] Service `apps/api/services/key_resolver.py` — lookup active key theo provider, cache 60s, fallback chain.
- [ ] Refactor các consumer (TTS route, transcript engine, embedder, RAG, worker LLM calls) dùng `key_resolver` thay vì đọc trực tiếp `os.environ`.
- [ ] Cost tracking: trigger hoặc batch job cộng `api_usage_logs.cost_usd` vào `current_month_cost_usd`.
- [ ] Cron reset cost đầu tháng (Supabase scheduled function).
- [ ] Alert generator: hourly check budget → insert `admin_alerts`.
- [ ] UI: `/admin/api-keys` table + form create + test button + rotate.
- [ ] UI: `/admin/alerts` list + resolve.

**Definition of Done**: admin thêm OpenAI key mới, test thành công, TTS vẫn chạy. Xoá key cũ → fallback chain pick key mới.

### Sprint A4 — Service Routing Config (1 tuần)
- [ ] CRUD `/api/admin/routing-config` + reload endpoint.
- [ ] Redis client wrapper (`apps/api/services/cache.py` + `apps/worker/services/config_watcher.py`).
- [ ] Worker: subscribe `routing:config:update` qua Redis pub/sub. Fallback polling 60s.
- [ ] Refactor `transcript_engine` (đã có), `tts` route, `embedder`, `ffmpeg` dispatcher (mới), `llm_analyzer` để đọc `service_routing_config` thay vì hard-code.
- [ ] Thêm `ffmpeg` dispatcher (`apps/worker/services/render_dispatcher.py`) gọi `Modal.render_video`.
- [ ] Cost estimate: query `api_usage_logs` 7 ngày gần nhất → avg cost per provider per feature.
- [ ] UI: `/admin/routing` 8 cards với dropdown + ordered fallback + toggle + cost preview.

**Definition of Done**: admin đổi primary provider cho `tts` từ `modal_omnivoice` → `elevenlabs` không cần restart worker. Job TTS mới dùng provider mới.

### Sprint A5 — Polish & Extended (1 tuần)
- [ ] Audit log viewer với full-text search + JSON diff viewer.
- [ ] Advanced dashboard analytics: cohort retention, top creators, revenue chart.
- [ ] Backup/restore config: dump `service_routing_config` + `credit_pricing` + `api_provider_keys.metadata` (không dump value) → JSON file.
- [ ] Documentation: `docs/admin_handbook.md` — cách dùng, troubleshooting, key rotation SOP.
- [ ] 2FA bắt buộc cho `super_admin` (Supabase MFA TOTP).
- [ ] IP whitelist enforcement test (chạy trên Caddy + FastAPI).

**Definition of Done**: admin mới onboard có thể đọc handbook + dùng đủ 4 nhóm chức năng mà không cần support.

---

## 2.8 Rủi ro & Mitigation

| # | Rủi ro | Mức độ | Mitigation |
|---|--------|--------|-----------|
| 1 | **Race condition khi 2 admin cùng edit routing config** | Trung bình | Optimistic locking: thêm column `config_version` (đã có ở schema). PATCH phải gửi `expected_version` → 409 nếu lệch. UI hiển thị "X đang sửa" realtime. |
| 2 | **Admin xoá nhầm user** | Cao | Soft delete + recovery window 7 ngày + bulk-undelete UI cho super_admin. Confirm dialog phải gõ email user để xác nhận. |
| 3 | **API key leak qua audit log** | Cao | Mask tất cả field `*key*`, `*secret*`, `*token*`, `*password*` ở `audit.py` helper. Unit test verify masking. Code review checklist. |
| 4 | **Panel bị brute force login** | Cao | Rate limit `/api/admin/**` (60 req/min). IP whitelist env. Supabase Auth lockout tự động. Caddy fail2ban integration optional. |
| 5 | **Worker không reload config khi Redis down** | Trung bình | Fallback polling DB mỗi 60s. Alert khi Redis pub/sub channel không nhận được message trong 5 phút. |
| 6 | **Impersonate token bị lạm dụng** | Cao | TTL tối đa 15 phút. Log mọi action với `impersonated_by`. Super_admin phải có lý do trong form. Có thể revoke token thủ công qua API. |
| 7 | **Vault secret mất / corrupted** | Thấp | Supabase Vault có backup managed. Backup script riêng dump metadata (không dump value) hàng tuần. |
| 8 | **Migration 0022 fail giữa chừng** | Trung bình | Migration viết trong transaction ngầm + test trên staging DB trước. Có rollback SQL đi kèm (`0022_admin_panel_rollback.sql`). |
| 9 | **API key hết budget giữa job** | Trung bình | Alert khi đạt 80% budget. Worker check budget trước mỗi call lớn (TTS, render). Nếu hết → fallback chain. |
| 10 | **Pricing config thay đổi làm user cũ mất tiền** | Thấp | Khi tăng giá → áp dụng từ job mới, job đang chạy giữ giá cũ. Khi giảm → áp dụng luôn cho tx chưa commit. |

---

## Phụ lục — Phụ thuộc vào kết quả Phần 1 (audit)

Các issue từ audit Phần 1 cần giải quyết **trước** khi sprint A1 bắt đầu (không thuộc admin panel nhưng liên quan):
- `hold_credits` duplicate giữa `0006` và `0020` → cleanup.
- RLS `transcripts` leaky → thắt chặt policy.
- Thêm 7 endpoint FastAPI còn thiếu (`/api/assistants`, `/api/jobs/trigger`, …) để admin có data thật để test.
- Đồng bộ CSS dark theme cho các trang legacy.

Nếu 4 issue trên chưa fix → admin panel sẽ chỉ thao tác trên data mock (kém giá trị khi demo).

---

## File output
Plan này lưu tại: `docs/plans/admin_panel_plan.md`

> Quyết định "chỉ plan, không code" đã được user chọn. Sau khi user duyệt plan, các sprint A1-A5 sẽ được thực thi tuần tự với báo cáo audit sau mỗi sprint.