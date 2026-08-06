# MSEW: phase11-analytics

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase11-analytics.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase11-analytics.md`
- **Admin Panel MVP xong (Phase 5-9):** Dashboard Phase 5 (4 stat cards).
- **Phase 10 đã xong:** MFA TOTP.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration `0028_analytics_views.sql` | `database-admin` | `backend-development` | `devops` |
| 2 | Service `analytics.py` | `backend-development` | `database-admin` | `debugging` |
| 3 | Router `admin_analytics.py` | `backend-development` | `better-auth` | `database-admin` |
| 4 | UPDATE `main.py` | `backend-development` | `debugging` | `code-review` |
| 5 | 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 6 | Dashboard UPDATE (3 charts) | `frontend-development` | `ui-styling` | `aesthetic` |
| 7 | Dashboard layout update | `frontend-development` | `ui-styling` | `debugging` |
| 8 | Self-verify | `debugging` | `code-review` | `devops` |

## Files KHÔNG được đụng (Do Not Touch)
- Phase 5-10 files (admin routers, audit, vault, routing, mfa, ip_whitelist).
- User-facing routes.
- Worker tasks.
- 4 stat cards dashboard Phase 5 (chỉ THÊM 3 charts bên dưới).

---

## Micro-Steps

### Step 1: Tạo `supabase/migrations/0028_analytics_views.sql`
**File:** `supabase/migrations/0028_analytics_views.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `backend-development`.
  - **Fallback:** `devops`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0028_analytics_views.sql
-- Purpose: Analytics RPC functions (cohort retention, revenue, top creators)
-- ============================================================

-- Index: optimize credit_transactions queries by created_at
CREATE INDEX IF NOT EXISTS idx_credit_tx_created ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_tx_action_created ON credit_transactions(action, created_at DESC);

-- RPC 1: revenue_by_day(days INT DEFAULT 30)
-- Returns: list of {day, total_credits_consumed, total_users}
CREATE OR REPLACE FUNCTION revenue_by_day(p_days INT DEFAULT 30)
RETURNS TABLE(day DATE, total_credits_consumed BIGINT, total_users BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('day', ct.created_at)::DATE AS day,
    SUM(ABS(ct.amount))::BIGINT AS total_credits_consumed,
    COUNT(DISTINCT ct.user_id)::BIGINT AS total_users
  FROM credit_transactions ct
  WHERE ct.action = 'consume'
    AND ct.created_at >= NOW() - (p_days || ' days')::INTERVAL
    AND p_days > 0
    AND p_days <= 90
  GROUP BY day
  ORDER BY day DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC 2: cohort_retention(cohort_weeks INT DEFAULT 8)
-- Cohort = week of user signup (Monday)
-- Returns: list of {cohort_week, week_offset, active_users, cohort_size, retention_pct}
CREATE OR REPLACE FUNCTION cohort_retention(p_cohort_weeks INT DEFAULT 8)
RETURNS TABLE(
  cohort_week DATE,
  week_offset INT,
  active_users BIGINT,
  cohort_size BIGINT,
  retention_pct NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH cohorts AS (
    SELECT
      DATE_TRUNC('week', u.created_at)::DATE AS cohort_week,
      u.id AS user_id
    FROM users u
    WHERE u.created_at >= NOW() - (p_cohort_weeks || ' weeks')::INTERVAL
  ),
  cohort_sizes AS (
    SELECT cohort_week, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_week
  )
  SELECT
    c.cohort_week,
    EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT AS week_offset,
    COUNT(DISTINCT act.user_id)::BIGINT AS active_users,
    cs.cohort_size::BIGINT,
    ROUND(COUNT(DISTINCT act.user_id)::NUMERIC / NULLIF(cs.cohort_size, 0), 4) AS retention_pct
  FROM cohorts c
  JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
  LEFT JOIN credit_transactions act ON act.user_id = c.user_id
    AND act.created_at >= c.cohort_week + (act.created_at - c.cohort_week)  -- any week after signup
  GROUP BY c.cohort_week, week_offset, cs.cohort_size
  HAVING EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT >= 0
    AND EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT < p_cohort_weeks
  ORDER BY c.cohort_week DESC, week_offset ASC
  LIMIT p_cohort_weeks * p_cohort_weeks;
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC 3: top_creators(metric TEXT DEFAULT 'assistants', max_limit INT DEFAULT 10)
-- metric: 'assistants' | 'credits_consumed'
-- Returns: list of {user_id, email, metric_value, tier, created_at}
CREATE OR REPLACE FUNCTION top_creators(p_metric TEXT DEFAULT 'assistants', p_limit INT DEFAULT 10)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  metric_value BIGINT,
  tier TEXT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  IF p_metric = 'assistants' THEN
    RETURN QUERY
    SELECT
      u.id,
      u.email,
      COUNT(ca.id)::BIGINT AS metric_value,
      u.tier,
      u.created_at
    FROM users u
    LEFT JOIN channel_assistants ca ON ca.user_id = u.id
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COUNT(ca.id) > 0
    ORDER BY metric_value DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSIF p_metric = 'credits_consumed' THEN
    RETURN QUERY
    SELECT
      u.id,
      u.email,
      COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT AS metric_value,
      u.tier,
      u.created_at
    FROM users u
    LEFT JOIN credit_transactions ct ON ct.user_id = u.id AND ct.action = 'consume'
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COALESCE(SUM(ABS(ct.amount)), 0) > 0
    ORDER BY metric_value DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSE
    RETURN;
  END IF;
END;
$$ LANGUAGE plpgsql STABLE;
```

**Verify command:**
```powershell
# Apply via Supabase Dashboard SQL Editor
```
**Expected:** 3 RPC functions + 2 indexes created.

---

### Step 2: Tạo `apps/api/services/analytics.py`
**File:** `apps/api/services/analytics.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Analytics service — RPC wrapper + Redis cache 5 phút.
3 RPC: revenue_by_day, cohort_retention, top_creators.
"""
from typing import Optional
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.cache import cache_get, cache_set


CACHE_TTL = 300  # 5 phút


def _cached_rpc(rpc_name: str, cache_key: str, params: dict) -> list:
    """Helper: cache_get → RPC fallback → cache_set."""
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    db = get_supabase_admin()
    result = db.rpc(rpc_name, params).execute()
    data = result.data or []
    
    cache_set(cache_key, data, ttl_seconds=CACHE_TTL)
    return data


def get_revenue_by_day(days: int = 30) -> dict:
    """
    Returns: {
        'days': [...],
        'credits_consumed': [...],
        'users_active': [...],
        'cached_at': ISO string,
    }
    """
    days = max(1, min(days, 90))
    cache_key = f'analytics:revenue:{days}d'
    data = _cached_rpc('revenue_by_day', cache_key, {'p_days': days})
    
    # Transform cho chart.js: day → list, credits → list
    return {
        'days': [row['day'] for row in reversed(data)],
        'credits_consumed': [int(row['total_credits_consumed'] or 0) for row in reversed(data)],
        'users_active': [int(row['total_users'] or 0) for row in reversed(data)],
        'cached_at': _now_iso(),
        'days_count': len(data),
    }


def get_cohort_retention(cohort_weeks: int = 8) -> dict:
    """
    Returns: {
        'cohorts': [
            {'week': '2026-07-27', 'retention': [1.0, 0.5, 0.3, ...]},
            ...
        ],
        'cached_at': ISO,
    }
    """
    cohort_weeks = max(1, min(cohort_weeks, 12))
    cache_key = f'analytics:cohort:{cohort_weeks}w'
    raw = _cached_rpc('cohort_retention', cache_key, {'p_cohort_weeks': cohort_weeks})
    
    # Group by cohort_week
    cohorts_dict: dict[str, dict] = {}
    for row in raw:
        cw = str(row['cohort_week'])
        if cw not in cohorts_dict:
            cohorts_dict[cw] = {'week': cw, 'cohort_size': int(row['cohort_size']), 'retention': []}
        # Ensure retention array has enough slots
        offset = row['week_offset']
        while len(cohorts_dict[cw]['retention']) <= offset:
            cohorts_dict[cw]['retention'].append(0.0)
        cohorts_dict[cw]['retention'][offset] = float(row['retention_pct'] or 0)
    
    return {
        'cohorts': list(cohorts_dict.values()),
        'cached_at': _now_iso(),
    }


def get_top_creators(metric: str = 'assistants', limit: int = 10) -> dict:
    """
    Returns: {
        'creators': [
            {'email': '...', 'metric_value': 5, 'tier': 'pro', 'created_at': '...'},
            ...
        ],
        'metric': str,
        'cached_at': ISO,
    }
    """
    metric = metric if metric in ('assistants', 'credits_consumed') else 'assistants'
    limit = max(1, min(limit, 100))
    cache_key = f'analytics:top_creators:{metric}:{limit}'
    data = _cached_rpc('top_creators', cache_key, {'p_metric': metric, 'p_limit': limit})
    
    return {
        'creators': [
            {
                'user_id': row['user_id'],
                'email': row['email'],
                'metric_value': int(row['metric_value']),
                'tier': row.get('tier', 'free'),
                'created_at': row['created_at'],
            }
            for row in data
        ],
        'metric': metric,
        'cached_at': _now_iso(),
    }


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def invalidate_all_caches() -> None:
    """Xóa tất cả analytics cache (admin trigger)."""
    from apps.api.services.cache import cache_delete
    for key in ['analytics:revenue:30d', 'analytics:cohort:8w', 'analytics:top_creators:assistants:10']:
        cache_delete(key)
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.services.analytics import get_revenue_by_day, get_cohort_retention, get_top_creators; print('analytics OK')"
```

**Expected output:** `analytics OK`.

---

### Step 3: Tạo `apps/api/routers/admin_analytics.py`
**File:** `apps/api/routers/admin_analytics.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `database-admin`.

**Code cần viết:**
```python
"""
Admin Analytics — 3 endpoints (revenue, cohort, top_creators).
Mounted dưới /api/admin/analytics.
"""
from fastapi import APIRouter, Depends, Query
from apps.api.dependencies.admin import require_admin
from apps.api.services.analytics import (
    get_revenue_by_day,
    get_cohort_retention,
    get_top_creators,
    invalidate_all_caches,
)


router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])


@router.get("/revenue")
async def revenue(
    admin_id: str = Depends(require_admin),
    days: int = Query(30, ge=1, le=90),
):
    """Revenue chart data. days: 1-90 (default 30)."""
    return get_revenue_by_day(days=days)


@router.get("/cohort")
async def cohort(
    admin_id: str = Depends(require_admin),
    weeks: int = Query(8, ge=1, le=12),
):
    """Cohort retention table. weeks: 1-12 (default 8)."""
    return get_cohort_retention(cohort_weeks=weeks)


@router.get("/top-creators")
async def top_creators(
    admin_id: str = Depends(require_admin),
    metric: str = Query('assistants', regex='^(assistants|credits_consumed)$'),
    limit: int = Query(10, ge=1, le=100),
):
    """Top creators by metric. metric: assistants | credits_consumed."""
    return get_top_creators(metric=metric, limit=limit)


@router.post("/cache/invalidate")
async def invalidate_cache(
    admin_id: str = Depends(require_admin),
):
    """Force invalidate analytics cache (admin manual trigger)."""
    invalidate_all_caches()
    return {'status': 'invalidated'}
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_analytics import router; print('admin_analytics OK')"
```

**Expected output:** `admin_analytics OK`.

---

### Step 4: UPDATE `apps/api/main.py` mount router
**File:** `apps/api/main.py` (UPDATE)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** Phase 10 admin imports, **THÊM:**
```python
from apps.api.routers.admin_analytics import router as admin_analytics_router
```

**SAU** Phase 10 admin mounts, **THÊM:**
```python
app.include_router(admin_analytics_router)
```

**Verify command:**
```powershell
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'analytics' in r.path]; print(len(routes), 'analytics routes'); [print(r) for r in sorted(routes)]"
```

**Expected output:** ≥ 4 routes (revenue, cohort, top-creators, cache/invalidate).

---

### Step 5: Tạo 3 web proxy routes
**Files (3 NEW):**
- `apps/web/app/api/admin/analytics/revenue/route.ts`
- `apps/web/app/api/admin/analytics/cohort/route.ts`
- `apps/web/app/api/admin/analytics/top-creators/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Pattern lặp lại:**

**`apps/web/app/api/admin/analytics/revenue/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const days = req.nextUrl.searchParams.get('days') || '30';
  try {
    const response = await apiFetch(`/api/admin/analytics/revenue?days=${days}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/analytics/cohort/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const weeks = req.nextUrl.searchParams.get('weeks') || '8';
  try {
    const response = await apiFetch(`/api/admin/analytics/cohort?weeks=${weeks}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/analytics/top-creators/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const metric = req.nextUrl.searchParams.get('metric') || 'assistants';
  const limit = req.nextUrl.searchParams.get('limit') || '10';
  try {
    const response = await apiFetch(`/api/admin/analytics/top-creators?metric=${metric}&limit=${limit}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 6: UPDATE `apps/web/app/(admin)/admin/dashboard/page.tsx`
**File:** `apps/web/app/(admin)/admin/dashboard/page.tsx` (UPDATE)
**Vai trò:** Thêm 3 charts (revenue + cohort + top creators).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Pre-step:** Cài `chart.js` + `react-chartjs-2`:
```powershell
cd d:\appDK\apps\web
pnpm add chart.js react-chartjs-2
```

**Code cần viết (UPDATE file hiện tại):**

**Thêm import đầu file:**
```typescript
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const Line = dynamic(() => import('react-chartjs-2').then(m => m.Line), { ssr: false });
```

**Thêm state + fetch logic trong component:**
```typescript
const [revenueData, setRevenueData] = useState<any>(null);
const [cohortData, setCohortData] = useState<any>(null);
const [topCreators, setTopCreators] = useState<any>(null);
const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

useEffect(() => {
  const days = timeRange === '7d' ? 7 : timeRange === '90d' ? 90 : 30;
  Promise.all([
    fetch(`/api/admin/analytics/revenue?days=${days}`).then(r => r.json()),
    fetch(`/api/admin/analytics/cohort?weeks=8`).then(r => r.json()),
    fetch(`/api/admin/analytics/top-creators?metric=assistants&limit=10`).then(r => r.json()),
  ]).then(([rev, coh, top]) => {
    setRevenueData(rev);
    setCohortData(coh);
    setTopCreators(top);
  });
}, [timeRange]);
```

**Thêm JSX trước closing `</div>` của root container (SAU 4 stat cards Phase 5):**
```tsx
{/* Phase 11: Analytics Charts */}
<div className="space-y-6 mt-8">
  <div className="flex items-center gap-3">
    <h2 className="text-2xl font-bold">Analytics</h2>
    <div className="ml-auto flex gap-2">
      {(['7d', '30d', '90d'] as const).map(r => (
        <button key={r} onClick={() => setTimeRange(r)}
          className={`px-3 py-1 rounded text-xs ${
            timeRange === r ? 'bg-[var(--brand-500)] text-white' : 'bg-[var(--surface)] border border-[var(--glass-border)]'
          }`}>
          {r}
        </button>
      ))}
    </div>
  </div>

  {/* Chart 1: Revenue */}
  {revenueData && (
    <div className="glass rounded-2xl p-5">
      <h3 className="text-lg font-semibold mb-3">Revenue ({revenueData.days_count} ngày)</h3>
      <Line
        data={{
          labels: revenueData.days,
          datasets: [
            {
              label: 'Credits Consumed',
              data: revenueData.credits_consumed,
              borderColor: 'rgb(99, 102, 241)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              tension: 0.3,
              fill: true,
            },
            {
              label: 'Active Users',
              data: revenueData.users_active,
              borderColor: 'rgb(236, 72, 153)',
              backgroundColor: 'rgba(236, 72, 153, 0.1)',
              tension: 0.3,
              yAxisID: 'y1',
            },
          ],
        }}
        options={{
          responsive: true,
          interaction: { mode: 'index', intersect: false },
          scales: {
            y: { type: 'linear', position: 'left', title: { display: true, text: 'Credits' } },
            y1: { type: 'linear', position: 'right', title: { display: true, text: 'Users' }, grid: { drawOnChartArea: false } },
          },
        }}
      />
      <p className="text-xs text-[var(--fg-tertiary)] mt-2">Updated: {new Date(revenueData.cached_at).toLocaleString('vi-VN')}</p>
    </div>
  )}

  {/* Chart 2: Cohort Retention Table */}
  {cohortData && (
    <div className="glass rounded-2xl p-5">
      <h3 className="text-lg font-semibold mb-3">Cohort Retention ({cohortData.cohorts.length} tuần)</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--glass-border)]">
              <th className="px-3 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Cohort</th>
              <th className="px-3 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Size</th>
              {Array.from({ length: 8 }, (_, i) => (
                <th key={i} className="px-3 py-2 text-center text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">W{i}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cohortData.cohorts.map((c: any) => (
              <tr key={c.week} className="border-b border-[var(--glass-border)]">
                <td className="px-3 py-2 font-mono text-xs">{c.week}</td>
                <td className="px-3 py-2 text-xs">{c.cohort_size}</td>
                {c.retention.map((r: number, idx: number) => (
                  <td key={idx} className="px-3 py-2 text-center text-xs">
                    <span className="inline-block px-2 py-0.5 rounded" style={{
                      backgroundColor: `rgba(99, 102, 241, ${r})`,
                      color: r > 0.5 ? 'white' : 'var(--fg-secondary)',
                    }}>
                      {(r * 100).toFixed(0)}%
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )}

  {/* Chart 3: Top Creators */}
  {topCreators && (
    <div className="glass rounded-2xl p-5">
      <h3 className="text-lg font-semibold mb-3">Top Creators ({topCreators.creators.length})</h3>
      <div className="space-y-2">
        {topCreators.creators.map((c: any, idx: number) => (
          <div key={c.user_id} className="flex items-center gap-3 bg-[var(--surface)] rounded-lg p-3">
            <span className="text-lg font-bold text-[var(--brand-300)] w-6">{idx + 1}</span>
            <div className="flex-1">
              <p className="text-sm font-semibold">{c.email}</p>
              <p className="text-xs text-[var(--fg-tertiary)]">
                {c.tier} · joined {new Date(c.created_at).toLocaleDateString('vi-VN')}
              </p>
            </div>
            <span className="text-2xl font-bold text-[var(--brand-300)]">{c.metric_value}</span>
            <span className="text-xs text-[var(--fg-tertiary)]">
              {topCreators.metric === 'assistants' ? 'assistants' : 'credits'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )}
</div>
```

**KHÔNG xóa:** 4 stat cards Phase 5.

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 7: Verify dashboard layout
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Verify command:**
```powershell
Get-Content "app\(admin)\admin\dashboard\page.tsx" | Select-String "Analytics|revenueData|cohortData|topCreators" | Measure-Object -Line
```

**Expected output:** ≥ 3 lines (đã có analytics section).

---

### Step 8: Self-verify
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `devops`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) All Python imports
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.analytics import get_revenue_by_day, get_cohort_retention, get_top_creators; print('analytics OK')"
python -c "from apps.api.routers.admin_analytics import router; print('admin_analytics OK')"

# 2) Admin analytics routes count
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'analytics' in r.path]; print(len(routes), 'analytics routes')"

# 3) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 4) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 5) UI dashboard có charts
Get-Content "app\(admin)\admin\dashboard\page.tsx" | Select-String "revenueData|cohortData|topCreators" | Measure-Object -Line

# 6) chart.js + react-chartjs-2 installed
Test-Path "node_modules\chart.js\package.json"
Test-Path "node_modules\react-chartjs-2\package.json"
```

**Expected output:**
- 3 dòng "OK"
- ≥ 4 analytics routes
- 2 tests PASSED
- 0 errors TS
- ≥ 3 chart references
- 2 packages installed = True

---

## Definition of Done cho Phase này
- Migration 0028 apply thành công (3 RPC functions + 2 indexes).
- 1 service mới (`analytics.py`) với Redis cache 5min.
- 1 router admin (4 endpoints: revenue + cohort + top-creators + cache invalidate).
- 3 web proxy routes.
- Dashboard UPDATE (3 charts).
- `chart.js` + `react-chartjs-2` installed.
- TS compile 0 errors.
- Existing pytest PASSED.
- 4 stat cards Phase 5 KHÔNG bị xóa (chỉ thêm charts bên dưới).
- Test RPC: revenue returns 30 rows, cohort returns ≥ 8 rows, top_creators returns 10 rows.
- Cache test: 2nd query < 100ms (Redis hit).
- KHÔNG file nào trong Phase 5-10 bị đụng ngoài `main.py` + `dashboard/page.tsx`.