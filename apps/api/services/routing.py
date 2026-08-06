"""
Service routing config — DB lookup + 60s cache.
Consumer gọi get_routing_config(feature) → return dict {primary, fallback_chain, enabled_providers, cost_per_call_usd}.
"""
import time
import threading
from typing import Optional, Dict, Any
from apps.api.services.cache import cache_get, cache_set, cache_delete


_CACHE: Dict[str, tuple[dict, float]] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 60  # seconds
_CACHE_KEY_PREFIX = 'routing:config:'
DEFAULT_CONFIG = {
    'primary_provider': None,
    'fallback_chain': [],
    'enabled_providers': {},
    'cost_per_call_usd': {},
}


def _load_from_db(feature: str) -> Optional[dict]:
    """Query service_routing_config table."""
    try:
        from apps.api.dependencies.supabase import get_supabase_admin
        db = get_supabase_admin()
        result = (
            db.table('service_routing_config')
            .select('*')
            .eq('feature', feature)
            .single()
            .execute()
        )
        if result.data:
            return {
                'primary_provider': result.data.get('primary_provider'),
                'fallback_chain': result.data.get('fallback_chain', []),
                'enabled_providers': result.data.get('enabled_providers', {}),
                'cost_per_call_usd': result.data.get('cost_per_call_usd', {}),
                'config_version': result.data.get('config_version', 1),
                'updated_at': result.data.get('updated_at'),
            }
    except Exception:
        pass
    return None


def get_routing_config(feature: str, use_cache: bool = True) -> dict:
    """
    Lấy routing config cho feature.
    
    Returns:
        dict với keys: primary_provider, fallback_chain, enabled_providers, cost_per_call_usd, ...
    
    Raises:
        Không raise. Nếu không tìm thấy → return DEFAULT_CONFIG.
    """
    # Check cache
    if use_cache:
        cached = _CACHE.get(feature)
        if cached:
            config, expires_at = cached
            if time.time() < expires_at:
                return config
    
    # DB lookup
    config = _load_from_db(feature)
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # Update cache
    with _CACHE_LOCK:
        _CACHE[feature] = (config, time.time() + _CACHE_TTL)
    
    # Also cache in Redis (optional, cho multi-process worker)
    cache_set(f'{_CACHE_KEY_PREFIX}{feature}', config, ttl_seconds=_CACHE_TTL)
    
    return config


def invalidate_cache(feature: Optional[str] = None) -> None:
    """Xóa cache cho feature (hoặc tất cả nếu feature is None)."""
    with _CACHE_LOCK:
        if feature:
            _CACHE.pop(feature, None)
            cache_delete(f'{_CACHE_KEY_PREFIX}{feature}')
        else:
            _CACHE.clear()


def get_all_routing_configs() -> list[dict]:
    """List tất cả routing configs (cho admin UI)."""
    try:
        from apps.api.dependencies.supabase import get_supabase_admin
        db = get_supabase_admin()
        result = (
            db.table('service_routing_config')
            .select('*')
            .order('feature')
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_cost_estimate(feature: str, window_days: int = 7) -> dict:
    """
    Query api_usage_logs 7d → avg cost per provider per feature.
    Returns: {provider: {avg_cost, total_calls, success_rate}, ...}
    """
    try:
        from apps.api.dependencies.supabase import get_supabase_admin
        db = get_supabase_admin()
        
        # Manual fallback
        result = (
            db.table('api_usage_logs')
            .select('provider_key_id, success, latency_ms, cost_usd, created_at')
            .gte('created_at', f'now() - interval \'{window_days} days\'')
            .execute()
        )
        
        logs = result.data or []
        # Group by provider_key_id (cần JOIN để lấy provider name — Phase 8 stub)
        provider_stats: dict[str, dict] = {}
        for log in logs:
            key_id = log.get('provider_key_id', 'unknown')
            stats = provider_stats.setdefault(key_id, {
                'total_calls': 0, 'success_calls': 0, 'latency_sum': 0, 'cost_sum': 0.0,
            })
            stats['total_calls'] += 1
            if log['success']:
                stats['success_calls'] += 1
                stats['cost_sum'] += log['cost_usd']
            stats['latency_sum'] += log['latency_ms']
        
        return {
            key_id: {
                'avg_cost_usd': stats['cost_sum'] / stats['success_calls'] if stats['success_calls'] > 0 else 0,
                'total_calls': stats['total_calls'],
                'success_rate': stats['success_calls'] / stats['total_calls'] if stats['total_calls'] > 0 else 0,
                'avg_latency_ms': stats['latency_sum'] / stats['total_calls'] if stats['total_calls'] > 0 else 0,
            }
            for key_id, stats in provider_stats.items()
        }
    except Exception:
        return {}