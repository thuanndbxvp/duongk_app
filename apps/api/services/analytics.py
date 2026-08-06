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