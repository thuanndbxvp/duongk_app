"""
Redis cache wrapper — pub/sub cho hot-reload + simple get/set.
Dùng cho routing config + key_resolver invalidation.
"""
import json
import os
import threading
from typing import Any, Callable, Optional
import redis


_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

_client: Optional[redis.Redis] = None
_lock = threading.Lock()


def get_client() -> redis.Redis:
    """Lazy singleton."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = redis.from_url(_REDIS_URL, decode_responses=True)
    return _client


def publish(channel: str, message: Any) -> int:
    """Publish message lên channel. Return số subscriber nhận."""
    payload = json.dumps(message) if not isinstance(message, str) else message
    return get_client().publish(channel, payload)


def subscribe(channel: str, callback: Callable[[str], None]) -> threading.Thread:
    """
    Subscribe channel → chạy callback trong thread riêng.
    Callback nhận message (string) làm input.
    """
    def listener():
        pubsub = get_client().pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    callback(message['data'])
                except Exception as e:
                    # Log nhưng không crash thread
                    import logging
                    logging.exception(f'Subscriber callback error: {e}')
    
    thread = threading.Thread(target=listener, daemon=True, name=f'redis-sub-{channel}')
    thread.start()
    return thread


def cache_get(key: str) -> Optional[Any]:
    """GET từ Redis cache. Auto-deserialize JSON."""
    val = get_client().get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    """SET vào Redis cache với TTL. Auto-serialize JSON."""
    payload = json.dumps(value) if not isinstance(value, str) else value
    get_client().setex(key, ttl_seconds, payload)


def cache_delete(key: str) -> None:
    """DELETE key."""
    get_client().delete(key)