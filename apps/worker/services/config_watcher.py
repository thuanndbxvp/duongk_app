"""
Config watcher — chạy trong Celery worker process.
Subscribe Redis channel 'routing:config:update' + fallback polling DB mỗi 60s.
Phase 8 KHÔNG tự động boot — phải gọi start_watcher() từ celery_app.py.
"""
import os
import threading
import time
import logging

logger = logging.getLogger(__name__)


_watcher_thread: threading.Thread = None
_last_known_versions: dict[str, int] = {}


def _on_routing_update(message: str):
    """Callback khi nhận Redis pub/sub message."""
    feature = message  # payload là feature name
    logger.info(f'[config_watcher] Routing config updated for feature: {feature}')
    
    try:
        from apps.api.services.routing import invalidate_cache
        invalidate_cache(feature)
    except Exception as e:
        logger.exception(f'[config_watcher] Failed to invalidate cache for {feature}: {e}')


def _polling_loop():
    """Fallback: poll DB mỗi 60s check updated_at."""
    from apps.api.dependencies.supabase import get_supabase_admin
    
    while True:
        try:
            db = get_supabase_admin()
            result = db.table('service_routing_config').select('feature, config_version, updated_at').execute()
            
            for row in (result.data or []):
                feature = row['feature']
                version = row.get('config_version', 1)
                if _last_known_versions.get(feature) != version:
                    if feature in _last_known_versions:
                        logger.info(f'[config_watcher] Detected config change for {feature} via polling (version {version})')
                        from apps.api.services.routing import invalidate_cache
                        invalidate_cache(feature)
                    _last_known_versions[feature] = version
        except Exception as e:
            logger.debug(f'[config_watcher] Polling iteration failed: {e}')
        
        time.sleep(60)


def start_watcher():
    """Boot watcher. Idempotent — chỉ start 1 lần."""
    global _watcher_thread
    
    if _watcher_thread is not None and _watcher_thread.is_alive():
        return
    
    # 1) Subscribe Redis
    try:
        from apps.api.services.cache import subscribe
        subscribe('routing:config:update', _on_routing_update)
        logger.info('[config_watcher] Subscribed to routing:config:update')
    except Exception as e:
        logger.warning(f'[config_watcher] Redis subscribe failed: {e}. Falling back to polling only.')
    
    # 2) Start polling fallback thread
    _watcher_thread = threading.Thread(target=_polling_loop, daemon=True, name='routing-config-watcher')
    _watcher_thread.start()
    logger.info('[config_watcher] Polling fallback thread started (60s interval)')