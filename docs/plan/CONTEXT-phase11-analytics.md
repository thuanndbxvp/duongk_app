# Bối cảnh Hệ thống (CONTEXT): phase11-analytics

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md`
- **Plan Admin Panel Phần 2:** `docs/plans/admin_panel_plan.md` (mục 2.7 — Sprint A5 extension)
- **Admin Panel MVP đã xong (Phase 5-9):** 13 features + Dashboard Phase 5 (4 stat cards).
- **Phase 10 đã xong:** MFA TOTP cho super_admin.
- **Đây là Phase 11 — Post-MVP Extension #2:** Advanced Dashboard Analytics.

## 2. Codebase Analysis (qua Read + Grep)

### Discovery — Dashboard Phase 5
- **`apps/web/app/(admin)/admin/dashboard/page.tsx`** — Phase 5 chỉ có 4 stat cards (total users, total credits, active jobs, error rate).
- **`apps/api/routers/admin_users.py`** (Phase 6) — Có `GET /api/admin/users/stats` (total users + new this month).
- **CHƯA CÓ** retention curve, revenue chart, top creators.

### Data schema khả dụng (qua Grep migrations)
| Table | Key columns | Dùng cho |
|-------|-------------|----------|
| `users` | `id, email, credits, tier, created_at` | New users / cohort / tier distribution |
| `credit_transactions` | `user_id, action, amount, balance_after, created_at` | Revenue (negative amounts) + top spenders |
| `api_usage_logs` | `user_id, feature, provider, cost_usd, success, created_at` | Cost analytics |
| `jobs` | `user_id, status, created_at` | Active jobs / completion rate |
| `channel_assistants` | `user_id, channel_name, created_at` | Top creators (user có nhiều assistant) |

### Hiện trạng cần thêm (qua Grep)
- ❌ **KHÔNG CÓ** `apps/api/services/analytics.py` (cohort + revenue + top).
- ❌ **KHÔNG CÓ** `apps/api/routers/admin_analytics.py` (4 endpoints).
- ❌ **KHÔNG CÓ** RPC `cohort_retention` + `revenue_by_day` + `top_creators`.
- ❌ **KHÔNG CÓ** UI charts trong dashboard.
- ❌ **KHÔNG CÓ** material view `daily_user_stats` (Phase 11 optional).

### Analytics features từ admin_panel_plan.md mục 2.7
Phase 11 implement **3 analytics** (scope tiết kiệm):
1. **Cohort retention** — % user quay lại sau N ngày.
2. **Revenue chart** — Tổng credit tiêu thụ (negative transactions) theo ngày.
3. **Top creators** — User có nhiều channel_assistants + nhiều credit tiêu thụ nhất.

Phase 11 KHÔNG implement:
- Predictive analytics (Phase 13+).
- Funnel analysis (Phase 14+).
- A/B test results (Phase 15+).

### Files KHÔNG tồn tại (cần tạo mới)
- `supabase/migrations/0028_analytics_views.sql` — 3 RPC function (cohort_retention, revenue_by_day, top_creators).
- `apps/api/services/analytics.py` — wrapper gọi RPC.
- `apps/api/routers/admin_analytics.py` — 3 endpoints.
- `apps/web/app/api/admin/analytics/{cohort,revenue,top-creators}/route.ts` — 3 web proxy.
- `apps/web/app/(admin)/admin/dashboard/page.tsx` (UPDATE) — thêm 3 charts.

### Files KHÔNG đụng
- Phase 5-10 files (admin routers, audit, vault, routing, mfa).
- User-facing routes.
- Worker tasks.

## 3. Các File liên quan và Vai trò

### Migration (1 NEW)
- `supabase/migrations/0028_analytics_views.sql` — 3 RPC functions:
  - `cohort_retention(cohort_weeks INT DEFAULT 8)` → list cohort + retention %.
  - `revenue_by_day(days INT DEFAULT 30)` → list ngày + total credits.
  - `top_creators(metric TEXT, limit INT DEFAULT 10)` → list user.

### Backend services (1 NEW)
- `apps/api/services/analytics.py` — wrapper gọi RPC + cache 5 phút.

### Backend routers (1 NEW)
- `apps/api/routers/admin_analytics.py` — 3 endpoints (cohort, revenue, top-creators).

### Frontend (3 web proxy + 1 UPDATE)
- 3 web proxy routes.
- Dashboard page UPDATE — thêm 3 charts (line chart revenue, retention table, top creators list).

## 4. Dependencies
- **External:** `chart.js` + `react-chartjs-2` (cần cài `pnpm add chart.js react-chartjs-2`). Phase 11 chỉ dùng khi UI đã có. Nếu Phase 11 chỉ implement backend, frontend Phase 12+ update.
- **Internal:** `apps.api.dependencies.admin.require_admin`.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Cache:** 5 phút (analytics query nặng, không real-time).
- **Backward compatible:** Dashboard Phase 5 4 stat cards KHÔNG bị xóa, chỉ thêm charts bên dưới.
- **Material view:** Phase 11 KHÔNG tạo material view (complex setup). Dùng RPC trực tiếp. Phase 12+ optimize.
- **Time range:** Default 30 ngày. Max 90 ngày (UI limit).

## 6. Output mong đợi

Sau Phase 11:
- Admin vào `/admin/dashboard` → thấy 4 stat cards (Phase 5) + 3 charts mới (Phase 11).
- **Chart 1: Revenue 30 ngày** — Line chart, x-axis = ngày, y-axis = credits consumed.
- **Chart 2: Cohort Retention** — Table 8 cột (Week 0 → Week 7), mỗi cell = % retention.
- **Chart 3: Top Creators** — Top 10 user có nhiều channel_assistants + credits consumed.
- Filter: chọn time range (7d / 30d / 90d) → update charts.

## 7. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- Migration 0028 apply thành công (3 RPC functions).
- 1 service mới (`analytics.py`).
- 1 router admin (3 endpoints).
- 3 web proxy routes.
- Dashboard UPDATE (3 charts).
- TS compile 0 errors.
- Existing pytest PASSED.
- Test RPC: cohort_retention returns 8 rows, revenue_by_day returns 30 rows, top_creators returns 10 rows.
- Test cache: query 2 lần liên tiếp → 2nd response time < 100ms (Redis cache hit).
- UI smoke: dashboard load charts không crash.