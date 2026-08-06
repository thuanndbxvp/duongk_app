"""
Key resolver — lookup API provider key theo provider name.
Cache 60s in-memory. Fallback chain: try env, then DB.
"""
import os
import time
from threading import Lock
from typing import Optional
from apps.api.services.vault import decrypt


_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_LOCK = Lock()
_CACHE_TTL = 60  # seconds


def resolve_key(provider: str) -> Optional[str]:
    """
    Resolve plaintext key cho provider.
    
    Priority:
    1. env var (PROVIDER_API_KEY uppercase) — backward compat
    2. DB lookup (api_provider_keys where provider=X and is_active=true and archived_at IS NULL)
    
    Returns:
        Plaintext key string, hoặc None nếu không tìm thấy.
    
    Cache: 60s in-memory (thread-safe).
    """
    # 1) Check env first (worker fallback Phase 7)
    env_var = f'{provider.upper().replace("-", "_")}_API_KEY'
    if provider == 'r2':
        env_var = 'R2_ACCESS_KEY_ID'
    elif provider == 'modal':
        env_var = 'MODAL_TOKEN_ID'
    elif provider == 'supabase_service_role':
        env_var = 'SUPABASE_SERVICE_ROLE_KEY'
    
    env_val = os.environ.get(env_var)
    if env_val:
        return env_val
    
    # 2) DB lookup with cache
    cached = _CACHE.get(provider)
    if cached:
        key, expires_at = cached
        if time.time() < expires_at:
            return key
    
    # DB lookup
    try:
        from apps.api.dependencies.supabase import get_supabase_admin
        db = get_supabase_admin()
        result = (
            db.table('api_provider_keys')
            .select('encrypted_value')
            .eq('provider', provider)
            .eq('is_active', True)
            .is_('archived_at', 'null')
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        if result.data and len(result.data) > 0:
            plaintext = decrypt(bytes(result.data[0]['encrypted_value']))
            with _CACHE_LOCK:
                _CACHE[provider] = (plaintext, time.time() + _CACHE_TTL)
            return plaintext
    except Exception:
        pass
    
    return None


def invalidate_cache(provider: Optional[str] = None):
    """Xóa cache. Gọi sau khi admin rotate key."""
    with _CACHE_LOCK:
        if provider:
            _CACHE.pop(provider, None)
        else:
            _CACHE.clear()


def get_active_keys_summary() -> dict[str, list[str]]:
    """
    List tất cả active keys per provider (chỉ labels, không value).
    Dùng cho admin UI.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    result = (
        db.table('api_provider_keys')
        .select('provider, label, is_active, last_test_status, current_month_cost_usd')
        .is_('archived_at', 'null')
        .order('provider, created_at', desc=True)
        .execute()
    )
    
    summary: dict[str, list[dict]] = {}
    for row in (result.data or []):
        summary.setdefault(row['provider'], []).append({
            'label': row['label'],
            'is_active': row['is_active'],
            'last_test_status': row.get('last_test_status'),
            'current_month_cost_usd': row.get('current_month_cost_usd', 0),
        })
    return summary