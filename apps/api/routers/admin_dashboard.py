"""
Admin Dashboard Stats — 4 top-line metrics.

Endpoints:
- GET /api/admin/dashboard/stats       → 4 stat cards (MRR + active_users_24h + jobs_today + credits_spent_today)
- GET /api/admin/dashboard/traffic    → 7-day sparkline (jobs/credit_tx/api_calls)
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin Dashboard"])


# Tier pricing (USD/month) — kept in sync with apps/web/app/(public)/pricing/page.tsx
TIER_PRICING_USD = {
    "free": 0,
    "pro": 29,
    "enterprise": 99,
}


def _start_of_today_utc() -> str:
    """ISO timestamp for 00:00 UTC today."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def _iso_hours_ago(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


@router.get("/stats")
async def stats(admin_id: str = Depends(require_admin)):
    """
    4 stat cards trên admin dashboard.

    MRR estimate: SUM(tier_pricing × user_count WHERE deleted_at IS NULL)
    Active users 24h: distinct user_id from jobs in last 24h
    Jobs today: COUNT(*) jobs created since 00:00 UTC
    Credits spent today: SUM(ABS(amount)) credit_transactions WHERE action='consume' AND created_at >= today
    """
    db = get_supabase_admin()

    # 1) MRR estimate — group users by tier
    users_by_tier_res = (
        db.table("users")
        .select("tier")
        .is_("deleted_at", "null")
        .execute()
    )
    tier_counts: dict[str, int] = {}
    for row in users_by_tier_res.data or []:
        t = row.get("tier", "free")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    mrr_estimate = sum(
        TIER_PRICING_USD.get(tier, 0) * count for tier, count in tier_counts.items()
    )

    # 2) Active users 24h — distinct user_id in jobs
    active_24h_res = (
        db.table("jobs")
        .select("user_id")
        .gte("created_at", _iso_hours_ago(24))
        .execute()
    )
    active_users_24h = len({row["user_id"] for row in (active_24h_res.data or []) if row.get("user_id")})

    # 3) Jobs today
    today_iso = _start_of_today_utc()
    jobs_today_res = (
        db.table("jobs")
        .select("id", count="exact")
        .gte("created_at", today_iso)
        .execute()
    )
    jobs_today = jobs_today_res.count or 0

    # 4) Credits spent today (action='consume', amount < 0)
    credits_today_res = (
        db.table("credit_transactions")
        .select("amount")
        .eq("action", "consume")
        .gte("created_at", today_iso)
        .execute()
    )
    credits_spent_today = sum(
        abs(int(row["amount"])) for row in (credits_today_res.data or []) if row.get("amount") is not None
    )

    # Bonus: tier breakdown (để UI có thể show pie chart)
    total_users = sum(tier_counts.values())

    return {
        "mrr_estimate_usd": mrr_estimate,
        "active_users_24h": active_users_24h,
        "jobs_today": jobs_today,
        "credits_spent_today": credits_spent_today,
        "tier_breakdown": {
            tier: {"count": count, "usd": count * TIER_PRICING_USD.get(tier, 0)}
            for tier, count in tier_counts.items()
        },
        "total_users": total_users,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/traffic")
async def traffic(admin_id: str = Depends(require_admin)):
    """
    7-day sparkline — jobs/credit_tx/api_calls per day.
    Dùng cho chart nhỏ trên dashboard (multi-line).
    """
    db = get_supabase_admin()
    now = datetime.now(timezone.utc)
    days = []

    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc).isoformat()
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc).isoformat()

        jobs_count = (
            db.table("jobs")
            .select("id", count="exact")
            .gte("created_at", day_start)
            .lte("created_at", day_end)
            .execute()
        ).count or 0

        tx_count = (
            db.table("credit_transactions")
            .select("id", count="exact")
            .gte("created_at", day_start)
            .lte("created_at", day_end)
            .execute()
        ).count or 0

        api_count = (
            db.table("api_usage_logs")
            .select("id", count="exact")
            .gte("created_at", day_start)
            .lte("created_at", day_end)
            .execute()
        ).count or 0

        days.append({
            "date": day.isoformat(),
            "jobs": jobs_count,
            "credit_tx": tx_count,
            "api_calls": api_count,
        })

    return {"days": days, "generated_at": datetime.now(timezone.utc).isoformat()}
