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