# MSEW: phase8-admin-routing-config

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase8-admin-routing-config.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase8-admin-routing-config.md`
- **Phase 5/6/7 đã xong:** admin router + audit + key_resolver + usage_tracker.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration `0026_service_routing_config.sql` | `database-admin` | `backend-development` | `devops` |
| 2 | Service `cache.py` | `backend-development` | `devops` | `debugging` |
| 3 | Service `routing.py` | `backend-development` | `database-admin` | `debugging` |
| 4 | Service `config_watcher.py` | `backend-development` | `devops` | `debugging` |
| 5 | Refactor `transcript/engine.py` | `backend-development` | `code-review` | `debugging` |
| 6 | Refactor `voice/routes.py` | `backend-development` | `code-review` | `debugging` |
| 7 | Refactor `rag/embedder.py` | `backend-development` | `code-review` | `debugging` |
| 8 | Refactor `worker/tasks/script_generate.py` | `backend-development` | `code-review` | `debugging` |
| 9 | Refactor `worker/tasks/analysis_task.py` | `backend-development` | `code-review` | `debugging` |
| 10 | Router `admin_routing.py` | `backend-development` | `better-auth` | `database-admin` |
| 11 | UPDATE `main.py` | `backend-development` | `debugging` | `code-review` |
| 12 | 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 13 | UI `admin/routing/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 14 | UPDATE `layout.tsx` | `frontend-development` | `ui-styling` | `debugging` |
| 15 | Self-verify | `debugging` | `code-review` | `devops` |

## Files KHÔNG được đụng (Do Not Touch)
- Phase 5/6/7 files (admin routers, audit, migration 0022-0025, key_resolver, vault).
- User-facing routes KHÔNG thuộc 5 consumer refactor.
- Worker task files KHÔNG thuộc routing (collect_channel, idea_generate, scene_breakdown).
- `transcript.routes.py` (wrapper, không consumer).
- `ffmpeg_render` + `thumbnail_vision` consumers (chưa có — Phase 9+).

---

## Micro-Steps

### Step 1: Tạo `supabase/migrations/0026_service_routing_config.sql`
**File:** `supabase/migrations/0026_service_routing_config.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `backend-development`.
  - **Fallback:** `devops`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0026_service_routing_config.sql
-- Purpose: Service routing config (DB-driven, hot-reload qua Redis pub/sub)
-- ============================================================

CREATE TABLE IF NOT EXISTS service_routing_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feature TEXT NOT NULL UNIQUE,
  primary_provider TEXT NOT NULL,
  fallback_chain TEXT[] NOT NULL DEFAULT '{}',
  enabled_providers JSONB NOT NULL DEFAULT '{}',
  cost_per_call_usd JSONB NOT NULL DEFAULT '{}',
  config_version INT NOT NULL DEFAULT 1,
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routing_feature ON service_routing_config(feature);

-- Seed default routing for 8 features
INSERT INTO service_routing_config (feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd) VALUES
  ('transcript_extract', 'supadata', ARRAY['youtube_transcript_api','modal_whisper'],
   '{"supadata":true,"youtube_transcript_api":true,"modal_whisper":true}'::jsonb,
   '{"supadata":0.001,"youtube_transcript_api":0,"modal_whisper":0.006}'::jsonb),
  ('llm_text', 'openai', ARRAY['stali']::TEXT[],
   '{"openai":true,"stali":true}'::jsonb,
   '{"openai":0.005,"stali":0.002}'::jsonb),
  ('embedding', 'cohere', ARRAY['openai']::TEXT[],
   '{"cohere":true,"openai":true}'::jsonb,
   '{"cohere":0.0001,"openai":0.00013}'::jsonb),
  ('emotion_classifier', 'openai', ARRAY[]::TEXT[],
   '{"openai":true}'::jsonb,
   '{"openai":0.0005}'::jsonb),
  ('ffmpeg_render', 'modal_t4', ARRAY['modal_a10g','local_cpu']::TEXT[],
   '{"modal_t4":true,"modal_a10g":true,"local_cpu":true}'::jsonb,
   '{"modal_t4":0.02,"modal_a10g":0.04,"local_cpu":0.0}'::jsonb),
  ('tts', 'modal_omnivoice', ARRAY['elevenlabs','openai_tts']::TEXT[],
   '{"modal_omnivoice":true,"elevenlabs":true,"openai_tts":true}'::jsonb,
   '{"modal_omnivoice":0.008,"elevenlabs":0.018,"openai_tts":0.015}'::jsonb),
  ('thumbnail_vision', 'openai', ARRAY['gemini']::TEXT[],
   '{"openai":true,"gemini":false}'::jsonb,
   '{"openai":0.0075,"gemini":0.0025}'::jsonb),
  ('footage_search', 'pexels', ARRAY['pixabay','unsplash']::TEXT[],
   '{"pexels":true,"pixabay":true,"unsplash":true}'::jsonb,
   '{"pexels":0,"pixabay":0,"unsplash":0}'::jsonb)
ON CONFLICT (feature) DO NOTHING;

-- Trigger: pg_notify khi UPDATE
CREATE OR REPLACE FUNCTION notify_routing_update() RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('routing:config:update', NEW.feature);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_routing_update ON service_routing_config;
CREATE TRIGGER trigger_routing_update
  AFTER UPDATE ON service_routing_config
  FOR EACH ROW
  WHEN (OLD.* IS DISTINCT FROM NEW.*)
  EXECUTE FUNCTION notify_routing_update();

-- RLS
ALTER TABLE service_routing_config ENABLE ROW LEVEL SECURITY;
-- service_role đọc/ghi; non-service default deny
```

**Verify command:**
```powershell
# Apply via Supabase Dashboard SQL Editor (copy/paste)
# Hoặc: supabase db push
```
**Expected:** 8 rows seeded, trigger active.

---

### Step 2: Tạo `apps/api/services/cache.py`
**File:** `apps/api/services/cache.py` (NEW)
**Vai trò:** Redis pub/sub wrapper.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `devops`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.services.cache import get_client, publish, subscribe, cache_get, cache_set, cache_delete; print('cache OK')"
```

**Expected output:** `cache OK`.

---

### Step 3: Tạo `apps/api/services/routing.py`
**File:** `apps/api/services/routing.py` (NEW)
**Vai trò:** DB lookup + 60s cache + Redis invalidate.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
        
        # Lấy recent usage
        result = db.rpc('api_usage_summary', {
            'p_feature': feature,
            'p_days': window_days,
        }).execute() if False else None  # Custom RPC nếu cần, fallback manual
        
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
```

**Verify command:**
```powershell
python -c "from apps.api.services.routing import get_routing_config, invalidate_cache, get_all_routing_configs, get_cost_estimate; print('routing OK')"
```

**Expected output:** `routing OK`.

---

### Step 4: Tạo `apps/worker/services/config_watcher.py`
**File:** `apps/worker/services/config_watcher.py` (NEW)
**Vai trò:** Worker subscribe Redis + polling fallback 60s.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `devops`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
python -c "from apps.worker.services.config_watcher import start_watcher; print('config_watcher OK')"
```

**Expected output:** `config_watcher OK`.

---

### Step 5: Refactor `apps/api/modules/transcript/engine.py`
**File:** `apps/api/modules/transcript/engine.py` (UPDATE — minimal)
**Vị trí:** Method `get_transcript()` (line 40-).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm import đầu file (sau line 12):**
```python
from apps.api.services.routing import get_routing_config
```

**Replace method `get_transcript` (line 40-80)** với:
```python
    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript với routing config từ DB.
        Fallback chain từ get_routing_config('transcript_extract').
        Graceful degradation: nếu routing fail → dùng tier cứng (backward compat).
        """
        routing = get_routing_config('transcript_extract')
        chain = [routing['primary_provider']] + routing.get('fallback_chain', [])
        enabled = routing.get('enabled_providers', {})
        
        for idx, provider in enumerate(chain):
            tier_num = idx + 1
            if not enabled.get(provider, False):
                continue
            
            try:
                if provider == 'youtube_transcript_api':
                    result = await self._fetch_youtube_api(video_id, preferred_languages)
                elif provider == 'supadata':
                    result = await self._fetch_supadata(video_id, preferred_languages)
                elif provider == 'modal_whisper':
                    result = await self._fetch_openai_whisper(video_id)
                else:
                    continue
                
                if result:
                    cost = routing.get('cost_per_call_usd', {}).get(provider, 0.0)
                    return {**result, "tier_used": tier_num, "estimated_cost_usd": cost, "provider_used": provider}
            except Exception as e:
                print(f"Tier {tier_num} ({provider}) failed: {e}")
        
        # Graceful degradation: nếu routing config rỗng, fallback tier cứng
        print('[transcript] Routing config empty, falling back to hardcoded tiers')
        return await self._legacy_get_transcript(video_id, preferred_languages)
```

**Thêm method legacy ở cuối class:**
```python
    async def _legacy_get_transcript(self, video_id, preferred_languages):
        """Backward compat: 3-tier hardcoded."""
        for tier_method in [self._fetch_youtube_api, self._fetch_supadata, self._fetch_openai_whisper]:
            try:
                result = await tier_method(video_id, preferred_languages)
                if result:
                    return result
            except Exception:
                continue
        return None
```

**Verify command:**
```powershell
python -c "from apps.api.modules.transcript.engine import TranscriptEngine; print('engine OK')"
```

**Expected output:** `engine OK`.

---

### Step 6: Refactor `apps/api/modules/voice/routes.py` (TTS provider)
**File:** `apps/api/modules/voice/routes.py` (UPDATE — append function + modify endpoint)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm import đầu file:**
```python
from apps.api.services.routing import get_routing_config
```

**Thêm function helper sau `get_s3_client`:**
```python
def select_tts_provider() -> str:
    """Chọn TTS provider từ routing config. Fallback env MODAL_TOKEN_ID."""
    routing = get_routing_config('tts')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    # Graceful fallback
    return os.environ.get('DEFAULT_TTS_PROVIDER', 'modal_omnivoice')
```

**KHÔNG sửa:** Logic R2 upload — R2 vẫn dùng env (chưa refactor key_resolver cho Phase 8).

**Verify command:**
```powershell
python -c "from apps.api.modules.voice.routes import select_tts_provider; print('voice OK')"
```

**Expected output:** `voice OK`.

---

### Step 7: Refactor `apps/api/modules/rag/embedder.py`
**File:** `apps/api/modules/rag/embedder.py` (UPDATE — minimal)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm import đầu file:**
```python
from apps.api.services.routing import get_routing_config
```

**Thêm method ở đầu class Embedder:**
```python
    def _select_embedding_provider(self) -> str:
        """Chọn embedding provider từ routing config."""
        routing = get_routing_config('embedding')
        primary = routing.get('primary_provider')
        if primary and routing.get('enabled_providers', {}).get(primary, False):
            return primary
        return 'cohere'  # fallback cứng
```

**KHÔNG sửa:** Logic embed_texts() — chỉ thêm helper. Phase 8 stub. Phase 9+ mới refactor method chính dùng helper này.

**Verify command:**
```powershell
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder OK')"
```

**Expected output:** `embedder OK`.

---

### Step 8: Refactor `apps/worker/tasks/script_generate.py` (LLM provider)
**File:** `apps/worker/tasks/script_generate.py` (UPDATE — minimal)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm import đầu file:**
```python
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.api.services.routing import get_routing_config
```

**Thêm function helper trước `@shared_task`:**
```python
def select_llm_provider() -> str:
    """Chọn LLM provider từ routing config. Fallback 'openai'."""
    routing = get_routing_config('llm_text')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    return 'openai'  # fallback cứng
```

**KHÔNG sửa:** Logic `generate_script()` — chỉ thêm helper. Phase 8 stub. Phase 9+ mới refactor method chính.

**Verify command:**
```powershell
python -c "from apps.worker.tasks.script_generate import select_llm_provider; print('script_generate OK')"
```

**Expected output:** `script_generate OK`.

---

### Step 9: Refactor `apps/worker/tasks/analysis_task.py` (emotion classifier)
**File:** `apps/worker/tasks/analysis_task.py` (UPDATE — minimal)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `code-review`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm import đầu file (tương tự script_generate):**
```python
from apps.api.services.routing import get_routing_config
```

**Thêm function helper:**
```python
def select_emotion_provider() -> str:
    """Chọn emotion classifier từ routing config. Fallback 'openai'."""
    routing = get_routing_config('emotion_classifier')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    return 'openai'  # fallback cứng
```

**KHÔNG sửa:** Logic analyze emotion — Phase 8 stub. Phase 9+ refactor method chính.

**Verify command:**
```powershell
python -c "from apps.worker.tasks.analysis_task import select_emotion_provider; print('analysis_task OK')"
```

**Expected output:** `analysis_task OK`.

---

### Step 10: Tạo `apps/api/routers/admin_routing.py`
**File:** `apps/api/routers/admin_routing.py` (NEW)
**Vai trò:** 5 endpoints.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `database-admin`.

**Code cần viết:**
```python
"""
Admin Service Routing Config — 5 endpoints.
Mounted dưới /api/admin/routing-config.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action
from apps.api.services.routing import (
    get_routing_config,
    invalidate_cache,
    get_all_routing_configs,
    get_cost_estimate,
)
from apps.api.services.cache import publish


router = APIRouter(prefix="/api/admin/routing-config", tags=["Admin Routing"])


class RoutingUpdate(BaseModel):
    primary_provider: Optional[str] = None
    fallback_chain: Optional[List[str]] = None
    enabled_providers: Optional[Dict[str, bool]] = None
    cost_per_call_usd: Optional[Dict[str, float]] = None
    expected_version: Optional[int] = None  # optimistic locking


@router.get("")
async def list_routing(
    admin_id: str = Depends(require_admin),
):
    """List tất cả routing configs (8 features)."""
    configs = get_all_routing_configs()
    # Attach cost estimate (cache 5min in production)
    for config in configs:
        config['cost_estimate_7d'] = get_cost_estimate(config['feature'], window_days=7)
    return configs


@router.get("/{feature}")
async def get_routing(
    feature: str,
    admin_id: str = Depends(require_admin),
):
    """Lấy routing config cho 1 feature."""
    config = get_routing_config(feature, use_cache=False)
    config['cost_estimate_7d'] = get_cost_estimate(feature, window_days=7)
    return config


@router.patch("/{feature}")
async def update_routing(
    feature: str,
    update: RoutingUpdate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """
    Update routing config.
    Optimistic locking: nếu expected_version != current → 409.
    Auto-publish Redis channel 'routing:config:update' (Postgres trigger cũng publish).
    """
    db = get_supabase_admin()
    
    before = db.table('service_routing_config').select('*').eq('feature', feature).single().execute().data
    if not before:
        raise HTTPException(404, 'Feature not found')
    
    # Optimistic locking
    if update.expected_version is not None and update.expected_version != before.get('config_version'):
        raise HTTPException(409, f"Config version mismatch (expected {update.expected_version}, current {before.get('config_version')})")
    
    update_data = update.dict(exclude_unset=True, exclude={'expected_version'})
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    update_data['config_version'] = before.get('config_version', 0) + 1
    update_data['updated_by'] = admin_id
    update_data['updated_at'] = 'now()'
    
    db.table('service_routing_config').update(update_data).eq('feature', feature).execute()
    after = db.table('service_routing_config').select('*').eq('feature', feature).single().execute().data
    
    # Invalidate cache
    invalidate_cache(feature)
    
    # Publish Redis channel (worker cũng nhận qua Postgres trigger, nhưng publish thẳng cho chắc)
    try:
        publish('routing:config:update', feature)
    except Exception:
        pass  # Fallback to polling
    
    # Audit log
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='routing.update',
        target_type='routing',
        target_id=feature,
        before={'primary_provider': before.get('primary_provider'), 'version': before.get('config_version')},
        after={'primary_provider': after.get('primary_provider'), 'version': after.get('config_version')},
        ip=request.client.host if request.client else None,
    )
    
    return after


@router.post("/{feature}/reload")
async def reload_routing(
    feature: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Force reload — invalidate cache + publish Redis channel."""
    invalidate_cache(feature)
    try:
        publish('routing:config:update', feature)
    except Exception:
        pass
    
    admin_email = get_supabase_admin().table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='routing.reload',
        target_type='routing',
        target_id=feature,
        reason='Manual reload routing config',
        ip=request.client.host if request.client else None,
    )
    
    return {'feature': feature, 'status': 'reload_queued'}


@router.get("/{feature}/cost-estimate")
async def cost_estimate(
    feature: str,
    admin_id: str = Depends(require_admin),
    window_days: int = 7,
):
    """Cost estimate cho 1 feature dựa trên api_usage_logs."""
    estimate = get_cost_estimate(feature, window_days=window_days)
    return {
        'feature': feature,
        'window_days': window_days,
        'provider_stats': estimate,
    }
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_routing import router; print('admin_routing OK')"
```

**Expected output:** `admin_routing OK`.

---

### Step 11: UPDATE `apps/api/main.py`
**File:** `apps/api/main.py` (UPDATE)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** Phase 7 admin imports, **THÊM:**
```python
from apps.api.routers.admin_routing import router as admin_routing_router
```

**SAU** Phase 7 admin mounts, **THÊM:**
```python
app.include_router(admin_routing_router)
```

**KHÔNG tự boot config_watcher trong main.py** (FastAPI không phải worker — chỉ Celery worker mới cần watcher).

**Verify command:**
```powershell
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'routing' in r.path]; print(len(routes), 'routing routes'); [print(r) for r in sorted(routes)]"
```

**Expected output:** ≥ 7 routes (list + get + patch + reload + cost-estimate + nested paths).

---

### Step 12: Tạo 3 web proxy routes
**Files (3 NEW):**
- `apps/web/app/api/admin/routing-config/route.ts`
- `apps/web/app/api/admin/routing-config/[feature]/route.ts`
- `apps/web/app/api/admin/routing-config/[feature]/reload/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Pattern lặp lại:**

**`apps/web/app/api/admin/routing-config/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const response = await apiFetch('/api/admin/routing-config', {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/routing-config/[feature]/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ feature: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { feature } = await params;
  try {
    const response = await apiFetch(`/api/admin/routing-config/${feature}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ feature: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { feature } = await params;
  const body = await req.json();
  try {
    const response = await apiFetch(`/api/admin/routing-config/${feature}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/routing-config/[feature]/reload/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ feature: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { feature } = await params;
  try {
    const response = await apiFetch(`/api/admin/routing-config/${feature}/reload`, { method: 'POST' }, token);
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

### Step 13: Tạo `apps/web/app/(admin)/admin/routing/page.tsx`
**File:** `apps/web/app/(admin)/admin/routing/page.tsx` (NEW)
**Vai trò:** 8 cards (mỗi feature 1 card) với dropdown + ordered fallback + toggle + cost preview.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

interface RoutingConfig {
  id: string;
  feature: string;
  primary_provider: string;
  fallback_chain: string[];
  enabled_providers: Record<string, boolean>;
  cost_per_call_usd: Record<string, number>;
  config_version: number;
  cost_estimate_7d?: Record<string, { avg_cost_usd: number; total_calls: number; success_rate: number }>;
}

const FEATURE_LABELS: Record<string, string> = {
  transcript_extract: 'Transcript Extract',
  llm_text: 'LLM Text (Script Gen)',
  embedding: 'Embedding (RAG)',
  emotion_classifier: 'Emotion Classifier',
  ffmpeg_render: 'FFmpeg Render',
  tts: 'Text-to-Speech',
  thumbnail_vision: 'Thumbnail Vision',
  footage_search: 'Footage Search',
};

export default function AdminRoutingPage() {
  const [configs, setConfigs] = useState<RoutingConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadConfigs();
  }, []);

  function loadConfigs() {
    setLoading(true);
    fetch('/api/admin/routing-config')
      .then((r) => r.json())
      .then(setConfigs)
      .finally(() => setLoading(false));
  }

  async function handleSave(config: RoutingConfig) {
    setSaving(config.feature);
    setMessage('');
    const res = await fetch(`/api/admin/routing-config/${config.feature}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_provider: config.primary_provider,
        fallback_chain: config.fallback_chain,
        enabled_providers: config.enabled_providers,
        cost_per_call_usd: config.cost_per_call_usd,
        expected_version: config.config_version,
      }),
    });
    if (res.ok) {
      setMessage(`✓ ${config.feature} updated (worker sẽ reload trong < 60s)`);
      loadConfigs();
    } else if (res.status === 409) {
      setMessage(`✗ Conflict — config đã bị sửa bởi admin khác. Reload.`);
      loadConfigs();
    } else {
      const err = await res.json();
      setMessage(`✗ Error: ${err.detail}`);
    }
    setSaving(null);
  }

  async function handleReload(feature: string) {
    await fetch(`/api/admin/routing-config/${feature}/reload`, { method: 'POST' });
    setMessage(`✓ ${feature} reload queued`);
  }

  if (loading) return <div className="p-8 text-center text-[var(--fg-tertiary)]">Loading…</div>;

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Service Routing</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{configs.length} features · Hot-reload qua Redis pub/sub</p>
      </div>

      {message && <div className="glass rounded-xl p-3 text-sm">{message}</div>}

      <div className="grid lg:grid-cols-2 gap-4">
        {configs.map((config) => (
          <RoutingCard
            key={config.feature}
            config={config}
            saving={saving === config.feature}
            onSave={handleSave}
            onReload={handleReload}
            onChange={setConfigs}
          />
        ))}
      </div>
    </div>
  );
}

function RoutingCard({
  config, saving, onSave, onReload, onChange,
}: {
  config: RoutingConfig;
  saving: boolean;
  onSave: (c: RoutingConfig) => void;
  onReload: (f: string) => void;
  onChange: (configs: RoutingConfig[]) => void;
}) {
  const allProviders = Array.from(new Set([
    config.primary_provider,
    ...config.fallback_chain,
    ...Object.keys(config.enabled_providers),
  ]));
  
  function updateConfig(patch: Partial<RoutingConfig>) {
    onChange([{ ...config, ...patch }]);
  }

  function moveProvider(idx: number, delta: number) {
    const chain = [...config.fallback_chain];
    const target = idx + delta;
    if (target < 0 || target >= chain.length) return;
    [chain[idx], chain[target]] = [chain[target], chain[idx]];
    updateConfig({ fallback_chain: chain });
  }

  return (
    <div className="glass rounded-2xl p-5 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold">{FEATURE_LABELS[config.feature] || config.feature}</h3>
          <p className="text-xs text-[var(--fg-tertiary)]">{config.feature} · v{config.config_version}</p>
        </div>
        <button
          onClick={() => onReload(config.feature)}
          className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400"
        >
          Reload
        </button>
      </div>

      {/* Primary provider */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Primary</label>
        <select
          value={config.primary_provider}
          onChange={(e) => updateConfig({ primary_provider: e.target.value })}
          className="w-full mt-1 px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white"
        >
          {allProviders.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* Fallback chain */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Fallback chain</label>
        <div className="mt-1 space-y-1">
          {config.fallback_chain.map((provider, idx) => (
            <div key={provider} className="flex items-center gap-2 bg-[var(--surface)] rounded-lg px-2 py-1">
              <span className="text-xs text-[var(--fg-tertiary)] w-6">{idx + 1}.</span>
              <span className="flex-1 text-sm">{provider}</span>
              <button onClick={() => moveProvider(idx, -1)} disabled={idx === 0} className="text-xs px-1 text-[var(--fg-tertiary)]">↑</button>
              <button onClick={() => moveProvider(idx, 1)} disabled={idx === config.fallback_chain.length - 1} className="text-xs px-1 text-[var(--fg-tertiary)]">↓</button>
            </div>
          ))}
        </div>
      </div>

      {/* Enabled providers */}
      <div>
        <label className="text-xs text-[var(--fg-tertiary)] uppercase tracking-wider">Enabled</label>
        <div className="mt-1 space-y-1">
          {allProviders.map(provider => (
            <label key={provider} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={config.enabled_providers[provider] ?? false}
                onChange={(e) => updateConfig({
                  enabled_providers: { ...config.enabled_providers, [provider]: e.target.checked },
                })}
              />
              <span className="flex-1">{provider}</span>
              <span className="text-xs text-[var(--fg-tertiary)]">
                ${config.cost_per_call_usd[provider]?.toFixed(4) || '0.0000'}/call
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Cost preview (7d) */}
      {config.cost_estimate_7d && Object.keys(config.cost_estimate_7d).length > 0 && (
        <div className="text-xs text-[var(--fg-tertiary)] space-y-1 bg-[var(--surface)] rounded-lg p-2">
          <p className="font-semibold">7d cost estimate:</p>
          {Object.entries(config.cost_estimate_7d).map(([keyId, stats]) => (
            <p key={keyId}>{keyId.slice(0, 8)}…: ${stats.avg_cost_usd.toFixed(4)} avg · {stats.total_calls} calls · {(stats.success_rate * 100).toFixed(1)}% success</p>
          ))}
        </div>
      )}

      <button
        onClick={() => onSave(config)}
        disabled={saving}
        className="w-full px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save + Hot Reload'}
      </button>
    </div>
  );
}
```

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 14: UPDATE `apps/web/app/(admin)/layout.tsx` enable Routing
**File:** `apps/web/app/(admin)/layout.tsx` (UPDATE)
**Vị trí:** Line 13 (`Routing`).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Code cần viết (1 lần `StrReplace`):**

**Thay — line 13:**
```typescript
  { href: '/admin/routing', label: 'Routing', icon: IconChannels, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/routing', label: 'Routing', icon: IconChannels, enabled: true },
```

**KHÔNG được sửa:**
- 7 mục còn lại (Dashboard, Users, Credits, Pricing, API Keys, Alerts, Audit Logs).
- Layout structure.

**Verify command:**
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "enabled:" | Measure-Object -Line
```

**Expected output:** 8 lines.

---

### Step 15: Self-verify toàn bộ (hot-reload + regression)
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `devops`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) All Python imports
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.cache import get_client, publish, subscribe; print('cache OK')"
python -c "from apps.api.services.routing import get_routing_config, invalidate_cache; print('routing OK')"
python -c "from apps.worker.services.config_watcher import start_watcher; print('config_watcher OK')"
python -c "from apps.api.routers.admin_routing import router; print('admin_routing OK')"

# 2) 5 consumer refactor imports
python -c "from apps.api.modules.transcript.engine import TranscriptEngine; print('engine OK')"
python -c "from apps.api.modules.voice.routes import select_tts_provider; print('voice OK')"
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder OK')"
python -c "from apps.worker.tasks.script_generate import select_llm_provider; print('script_generate OK')"
python -c "from apps.worker.tasks.analysis_task import select_emotion_provider; print('analysis_task OK')"

# 3) Admin routes count (routing only)
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'routing' in r.path]; print(len(routes), 'routing routes')"

# 4) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 5) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 6) UI page exists
Test-Path "app\(admin)\admin\routing\page.tsx"

# 7) Hot-reload smoke test (manual)
# - Start Redis: docker run -p 6379:6379 redis (nếu chưa)
# - Start worker: cd apps/worker && celery -A celery_app worker --loglevel=info
# - Trong worker logs, sẽ thấy: "[config_watcher] Subscribed to routing:config:update"
# - Admin PATCH /api/admin/routing-config/tts qua UI
# - Trong worker logs, sẽ thấy: "[config_watcher] Routing config updated for feature: tts"
# - Gọi /admin/routing → click "Reload" trên card
```

**Expected output:**
- 10 dòng "OK"
- ≥ 7 routing routes
- 2 tests PASSED
- 0 errors TS
- 1 UI page = True

---

## Definition of Done cho Phase này
- Migration 0026 apply thành công (8 features seeded + trigger active).
- `cache.py` (Redis pub/sub) + `routing.py` (DB lookup + cache) + `config_watcher.py` (worker) services.
- 5 consumer refactor (transcript/voice/embedder/script_generate/analysis_task) có helper `select_*_provider()`.
- 5 endpoint admin mới (`/api/admin/routing-config/*`).
- 3 web proxy + 1 trang admin `/admin/routing` + sidebar enable.
- TS compile 0 errors.
- Existing pytest PASSED.
- Hot-reload verified: admin save → worker nhận signal trong < 60s (qua Redis pub/sub hoặc polling).
- Graceful degradation: nếu routing config rỗng → consumer fallback env var cũ (TTS vẫn chạy với MODAL_TOKEN_ID).
- KHÔNG file nào trong Phase 5/6/7 bị đụng ngoài `main.py` (chỉ thêm router mount).