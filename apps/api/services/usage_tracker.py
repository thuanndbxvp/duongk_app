"""
Usage tracker — decorator log API call + cost sau khi worker call provider.
Phase 7 chỉ track. Cron reset cost đầu tháng = Phase 9+.
"""
import time
import functools
from datetime import datetime, timezone


def track_usage(provider: str, feature: str = None, cost_per_call_usd: float = 0.0):
    """
    Decorator: track API call + cost + latency.
    
    Usage:
        @track_usage('openai', 'llm_text', cost_per_call_usd=0.005)
        def call_openai(...):
            ...
    
    Logs vào api_usage_logs. Update current_month_cost_usd.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            success = True
            error_code = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_code = type(e).__name__
                raise
            finally:
                latency_ms = int((time.time() - start) * 1000)
                _log_usage(provider, feature or func.__name__, success, latency_ms, cost_per_call_usd, error_code)
        return wrapper
    return decorator


def _log_usage(provider: str, feature: str, success: bool, latency_ms: int, cost_usd: float, error_code=None):
    """Insert vào api_usage_logs. Update current_month_cost_usd."""
    try:
        from apps.api.dependencies.supabase import get_supabase_admin
        db = get_supabase_admin()
        
        # 1) Get active key id
        key = (
            db.table('api_provider_keys')
            .select('id')
            .eq('provider', provider)
            .eq('is_active', True)
            .is_('archived_at', 'null')
            .limit(1)
            .execute()
        )
        if not key.data:
            return  # No active key, skip tracking
        
        key_id = key.data[0]['id']
        
        # 2) Insert log
        db.table('api_usage_logs').insert({
            'provider_key_id': key_id,
            'feature': feature,
            'success': success,
            'latency_ms': latency_ms,
            'cost_usd': cost_usd if success else 0,
            'error_code': error_code,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }).execute()
        
        # 3) Update current_month_cost_usd (idempotent — chỉ +cost_usd nếu success)
        if success and cost_usd > 0:
            db.rpc('increment_monthly_cost', {
                'p_key_id': key_id,
                'p_amount': cost_usd,
            }).execute() if False else None  # RPC chưa có, skip Phase 7
    
    except Exception:
        pass  # Tracking fail không ảnh hưởng main flow