# Phân bổ Kỹ năng (SKILL-ROUTING): phase11-analytics

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 11 là **Post-MVP Extension #2** — Advanced Dashboard Analytics. Phase mở rộng Dashboard Phase 5 với 3 analytics: cohort retention + revenue chart + top creators.

Skill chính: `database-admin` (RPC functions + indexes) + `backend-development` (service wrapper + cache) + `frontend-development` (chart.js + react-chartjs-2).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Migration `0028_analytics_views.sql` | `database-admin` | `backend-development` | `devops` | 3 RPC functions (PL/pgSQL) |
| Step 2 | Service `analytics.py` | `backend-development` | `database-admin` | `debugging` | RPC wrapper + Redis cache 5min |
| Step 3 | Router `admin_analytics.py` | `backend-development` | `better-auth` | `database-admin` | 3 endpoints |
| Step 4 | UPDATE `main.py` mount router | `backend-development` | `debugging` | `code-review` | Integration |
| Step 5 | 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` | Next.js proxy |
| Step 6 | UI dashboard UPDATE (3 charts) | `frontend-development` | `ui-styling` | `aesthetic` | chart.js line + retention table + top list |
| Step 7 | UPDATE dashboard page layout | `frontend-development` | `ui-styling` | `debugging` | Layout update |
| Step 8 | Self-verify | `debugging` | `code-review` | `devops` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `database-admin`: PL/pgSQL functions + index optimization.
- `backend-development`: Cache pattern + service wrapper.
- `frontend-development`: chart.js integration + responsive layout.
- `code-review`: Verify SQL không full table scan trên production data.
- `devops`: Redis cache TTL tuning.

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** sửa Phase 5-10 files (ngoại trừ `main.py` mount + dashboard page).
- ❌ **CẤM** xóa 4 stat cards Phase 5 (chỉ thêm charts).
- ❌ **CẤM** RPC function full table scan KHÔNG có LIMIT.
- ❌ **CẤM** cache TTL > 10 phút (analytics stale OK nhưng KHÔNG quá stale).
- ❌ **CẤM** frontend dependency KHÔNG trong package.json (cần install `chart.js` + `react-chartjs-2`).
- ❌ **CẤM** commit RPC test data thật vào migration.
- ❌ **CẤM** analytics queries query > 90 ngày (UI limit).
- ❌ **CẤM** mutation admin_analytics router (read-only).
- ❌ **CẤM** đụng user-facing routes.
- ❌ **CẤM** đụng audit log (analytics KHÔNG ghi log).