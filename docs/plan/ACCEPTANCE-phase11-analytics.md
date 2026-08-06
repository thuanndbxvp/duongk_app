# Tiêu chí Nghiệm thu (ACCEPTANCE): phase11-analytics

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `supabase/migrations/0028_analytics_views.sql` (NEW)
- [ ] Có 2 indexes mới: `idx_credit_tx_created`, `idx_credit_tx_action_created`.
- [ ] RPC `revenue_by_day(p_days INT DEFAULT 30)` → TABLE(day DATE, total_credits_consumed BIGINT, total_users BIGINT).
- [ ] RPC `cohort_retention(p_cohort_weeks INT DEFAULT 8)` → TABLE(cohort_week DATE, week_offset INT, active_users BIGINT, cohort_size BIGINT, retention_pct NUMERIC).
- [ ] RPC `top_creators(p_metric TEXT, p_limit INT DEFAULT 10)` → TABLE(user_id UUID, email TEXT, metric_value BIGINT, tier TEXT, created_at TIMESTAMPTZ).
- [ ] Tất cả RPC có validation: `p_days BETWEEN 1 AND 90`, `p_cohort_weeks BETWEEN 1 AND 12`, `p_metric IN ('assistants', 'credits_consumed')`.
- [ ] Tất cả RPC dùng `LANGUAGE plpgsql STABLE`.

### File 2: `apps/api/services/analytics.py` (NEW)
- [ ] Có hàm `get_revenue_by_day(days=30) → dict` (cached 5min).
- [ ] Có hàm `get_cohort_retention(cohort_weeks=8) → dict` (cached 5min).
- [ ] Có hàm `get_top_creators(metric='assistants', limit=10) → dict` (cached 5min).
- [ ] Có hàm `invalidate_all_caches()` cho admin manual trigger.
- [ ] Cache key format: `analytics:revenue:{days}d`, `analytics:cohort:{weeks}w`, `analytics:top_creators:{metric}:{limit}`.

### File 3: `apps/api/routers/admin_analytics.py` (NEW)
- [ ] Có 4 endpoints:
  - `GET /api/admin/analytics/revenue?days=N` (1-90, default 30)
  - `GET /api/admin/analytics/cohort?weeks=N` (1-12, default 8)
  - `GET /api/admin/analytics/top-creators?metric=&limit=` (regex validation)
  - `POST /api/admin/analytics/cache/invalidate` (manual cache clear)
- [ ] Mọi endpoint có `Depends(require_admin)`.

### File 4: `apps/api/main.py` (UPDATE)
- [ ] Có import mới: `admin_analytics_router`.
- [ ] Có `app.include_router(admin_analytics_router)`.
- [ ] Admin analytics route count ≥ 4.

### File 5-7: Web proxy routes (3 NEW)
- [ ] `apps/web/app/api/admin/analytics/revenue/route.ts` (GET).
- [ ] `apps/web/app/api/admin/analytics/cohort/route.ts` (GET).
- [ ] `apps/web/app/api/admin/analytics/top-creators/route.ts` (GET).
- [ ] TS compile 0 errors.

### File 8: `apps/web/app/(admin)/admin/dashboard/page.tsx` (UPDATE)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] 4 stat cards Phase 5 KHÔNG bị xóa.
- [ ] Có time range filter (7d/30d/90d).
- [ ] **Chart 1: Revenue** — Line chart 2 lines (Credits Consumed + Active Users) + 2 y-axis.
- [ ] **Chart 2: Cohort Retention** — Table 10 cols (Cohort + Size + W0-W7), mỗi cell color-coded theo retention %.
- [ ] **Chart 3: Top Creators** — List top 10 với email + tier + metric_value.
- [ ] "Updated" timestamp hiển thị cho revenue chart.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Performance:**
  - Cache hit: < 100ms response time.
  - Cache miss: < 2s response time (Postgres RPC + Redis set).
  - 3 API song song dùng `Promise.all`.
- **Backward compatibility:**
  - 4 stat cards Phase 5 KHÔNG bị xóa.
  - 32 admin endpoints Phase 5-9 vẫn hoạt động bình thường.
  - 5 endpoints Phase 10 MFA vẫn hoạt động.
- **No new database lock:**
  - RPC `STABLE` (không lock table).
  - Indexes mới (không impact INSERT/UPDATE).
- **Frontend bundle:**
  - chart.js dynamic import (chỉ load trên dashboard).
  - ssr: false (chart.js cần window).
- **UX:**
  - Time range filter rõ ràng (7d/30d/90d).
  - Updated timestamp.
  - Empty state (no data) hiển thị "No data" thay crash.

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 11 KHÔNG thêm unit test mới. Verify qua smoke test:
  - RPC revenue returns ≤ 30 rows.
  - RPC cohort returns ≤ 64 rows (8 cohort × 8 weeks).
  - RPC top_creators returns ≤ 10 rows.
  - Cache: 2nd query < 100ms (Redis hit).
- **Frontend:** TS compile 0 errors.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Install frontend deps
```powershell
cd d:\appDK\apps\web
pnpm add chart.js react-chartjs-2
```
**Expected:** 2 packages added to package.json.

### Bước 2: Verify Python imports (3 file)
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.analytics import get_revenue_by_day, get_cohort_retention, get_top_creators; print('analytics OK')"
python -c "from apps.api.routers.admin_analytics import router; print('admin_analytics OK')"
```
**Expected:** 3 dòng "OK".

### Bước 3: Verify admin analytics routes count
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'analytics' in r.path]); print(len(routes), 'analytics routes'); [print(r) for r in routes]"
```
**Expected:** ≥ 4 routes.

### Bước 4: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 5: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 6: Verify dashboard có 3 charts
```powershell
Get-Content "app\(admin)\admin\dashboard\page.tsx" | Select-String "revenueData|cohortData|topCreators" | Measure-Object -Line
```
**Expected:** ≥ 3 matches.

### Bước 7: chart.js packages installed
```powershell
Test-Path "node_modules\chart.js\package.json"
Test-Path "node_modules\react-chartjs-2\package.json"
```
**Expected:** 2 True.

### Bước 8: Apply migration
```powershell
# Via Supabase Dashboard SQL Editor (copy/paste 0028_analytics_views.sql)
# Hoặc: supabase db push
```
**Expected:** Migration applied, 3 RPC functions visible trong dashboard.

### Bước 9: Test RPC functions (Postgres client)
```sql
SELECT * FROM revenue_by_day(30);        -- Returns ≤ 30 rows
SELECT * FROM cohort_retention(8);       -- Returns ≤ 64 rows
SELECT * FROM top_creators('assistants', 10);  -- Returns 10 rows
```
**Expected:** 3 queries return rows không lỗi.

### Bước 10: Visual smoke test (optional, cần admin role)
```powershell
pnpm dev
```
Mở browser với admin user:
- `/admin/dashboard` → 4 stat cards (Phase 5) + 3 charts (Phase 11).
- Click time range filter (7d/30d/90d) → revenue chart updates.
- Cohort table hiển thị retention % color-coded.
- Top creators list hiển thị 10 creators.
- "Updated" timestamp hiển thị.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 8 MSEW step phải PASS verify command của riêng nó, VÀ 10 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase11-analytics.md` và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Phase 12+)
Sau khi analytics cơ bản xong, có thể tiếp tục:
- **Material view** (`daily_user_stats`) — optimize cho 90-day query (Phase 12+).
- **Predictive analytics** — ML forecast retention/revenue (Phase 13+).
- **Funnel analysis** — track conversion từ signup → first job → paid tier (Phase 14+).
- **A/B test results** — Phase 15+.
- **Cohort drill-down** — click cohort → xem list user cụ thể (Phase 16+).
- **Export analytics PDF** — share với stakeholders (Phase 17+).

Hoặc chuyển sang phase khác:
- **Phase 12: Backup cron** (schedule job dump config → S3).
- **Phase 13: ffmpeg_render dispatcher** (Modal.render_video).
- **Phase 14: thumbnail_vision consumer** (Phase 8 routing wire).
- **Phase 15: Caddy IP whitelist** (defense in depth layer 2).
- **Phase 16: Audit log retention** (archive > 1 năm).