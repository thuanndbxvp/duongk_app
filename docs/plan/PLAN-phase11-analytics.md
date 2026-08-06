# Kế hoạch Triển khai (PLAN): phase11-analytics

## 1. Mục tiêu (Objective)
- **Mô tụ ngắn gọn:** Post-MVP Extension #2 — Advanced Dashboard Analytics. Mở rộng Dashboard Phase 5 với 3 charts: cohort retention + revenue chart + top creators.
- **Giá trị cốt lõi:**
  1. Admin hiểu user retention (% user quay lại sau N ngày).
  2. Admin thấy revenue trend (credit consumed theo ngày).
  3. Admin identify top creators (Power user → cần support tốt hơn).

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: RPC functions (Postgres) + Service cache (Redis) + Chart.js UI
```
[Admin Dashboard]
  → GET /api/admin/analytics/revenue?days=30
    → Redis cache check (key=analytics:revenue:30d, ttl=300s)
      → Cache hit: return
      → Cache miss: SELECT revenue_by_day(30) RPC
    → Return JSON → Line chart (chart.js)

[PostgreSQL RPC]
  revenue_by_day(days INT) RETURNS TABLE(day DATE, total_credits_consumed BIGINT)
  → Query credit_transactions WHERE action='consume' GROUP BY day
  → Index idx_credit_tx_created (Phase 11 NEW)

cohort_retention(cohort_weeks INT) RETURNS TABLE(cohort_week DATE, week_offset INT, active_users BIGINT)
  → Cohort = tuần signup của user
  → Tính active_users cho mỗi week_offset (0-7 tuần sau signup)

top_creators(metric TEXT, limit INT) RETURNS TABLE(...)
  → metric='assistants' → ORDER BY COUNT(channel_assistants) DESC
  → metric='credits_consumed' → ORDER BY SUM(amount) DESC WHERE action='consume'
```

### Cấu trúc file
```
supabase/migrations/
  0028_analytics_views.sql             (NEW) - 3 RPC functions + 1 index

apps/api/services/
  analytics.py                         (NEW) - RPC wrapper + Redis cache 5min

apps/api/routers/
  admin_analytics.py                   (NEW) - 3 endpoints

apps/api/main.py                       (UPDATE) - mount router

apps/web/app/api/admin/analytics/
  cohort/route.ts                      (NEW) - GET retention
  revenue/route.ts                     (NEW) - GET revenue
  top-creators/route.ts                (NEW) - GET top creators

apps/web/app/(admin)/admin/dashboard/
  page.tsx                             (UPDATE) - 4 stat cards + 3 charts
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Material view (đã loại)
- **Lý do loại:** Setup complex + refresh job. Phase 11 dùng RPC trực tiếp với cache 5 phút. Phase 12+ nâng cấp material view nếu cần.

### Phương án B — ClickHouse / BigQuery (ĐÃ LOẠI)
- **Lý do loại:** Chưa cần scale. PostgreSQL RPC đủ cho ~10k users.

### Phương án C — Recharts thay vì chart.js (ĐÃ LOẢI một phần)
- **Lý do loại:** chart.js bundle nhỏ hơn (~80KB vs ~200KB Recharts). Phase 11 dùng chart.js.

### Phương án D — Phase 11 chỉ backend (ĐÃ LOẢI một phần)
- **Lý do loại:** Cần UI để admin dùng. Phase 11 backend + UI cùng lúc.

### Lý do chọn phương án hiện tại
- **RPC functions:** Tính toán server-side, trả kết quả tổng hợp.
- **Redis cache 5min:** Balance freshness vs DB load.
- **Chart.js:** Lightweight, responsive, có line/bar/pie.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | RPC query chậm (> 5s) trên data lớn | **Cao** | Index `idx_credit_tx_created` + LIMIT + cache 5min. |
| 2 | Cache stale 5min → admin thấy data cũ | Thấp | Acceptable cho analytics. UI hiển thị "Updated 2 min ago". |
| 3 | chart.js bundle lớn → load time chậm | Thấp | Dynamic import (`next/dynamic`) load chart chỉ trên dashboard. |
| 4 | Cohort retention sai số (timezone bug) | Trung bình | Dùng `date_trunc('week', created_at)` UTC. |
| 5 | Top creators query full scan | Trung bình | ORDER BY indexed column + LIMIT 10. |
| 6 | Dashboard load chậm do 3 API song song | Thấp | Promise.all([...]) + parallel fetch. |
| 7 | Chart.js SSR error | Thấp | `dynamic(import, { ssr: false })`. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~700 lines (100 SQL PL/pgSQL + 150 Python service + 100 Python router + 150 TypeScript + 200 React dashboard) |
| **Timeline** | 8 steps MSEW, ước tính 4-5 giờ Tier 2 thực thi + verify |
| **Files touched** | 7 NEW + 2 UPDATE (1 migration + 1 service + 1 router + 3 proxy + 1 dashboard + 1 main.py) |

## 6. Phụ thuộc giữa các Step
- Step 1 (migration) → tạo RPC functions + index.
- Step 2 (analytics.py) → gọi RPC + cache.
- Step 3 (router) → Step 4 (main.py mount).
- Step 5 (3 web proxy) → Step 6 (dashboard).
- Step 7 (dashboard layout) sau Step 6.
- Step 8 (verify) cuối cùng.