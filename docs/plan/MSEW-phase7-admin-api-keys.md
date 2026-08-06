# MSEW: phase7-admin-api-keys

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase7-admin-api-keys.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase7-admin-api-keys.md`
- **Phase 5 đã xong:** `require_admin` + `audit.py:log_admin_action` + migration 0022.
- **Phase 6 đã xong:** 3 routers admin (users/credit/pricing) + 3 trang UI + sidebar enable Users/Credits.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF
- **Dependency cần cài:** `pip install cryptography` (Fernet).

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration `0023_api_provider_keys.sql` | `database-admin` | `backend-development` | `devops` |
| 2 | Migration `0024_api_usage_logs.sql` | `database-admin` | `backend-development` | `debugging` |
| 3 | Migration `0025_admin_alerts.sql` | `database-admin` | `backend-development` | `debugging` |
| 4 | Service `vault.py` | `backend-development` | `devops` | `debugging` |
| 5 | Service `key_resolver.py` | `backend-development` | `database-admin` | `debugging` |
| 6 | Service `usage_tracker.py` | `backend-development` | `database-admin` | `debugging` |
| 7 | Router `admin_api_keys.py` | `backend-development` | `better-auth` | `database-admin` |
| 8 | Router `admin_alerts.py` | `backend-development` | `database-admin` | `debugging` |
| 9 | UPDATE `main.py` | `backend-development` | `debugging` | `code-review` |
| 10 | 5 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 11 | UI `admin/api-keys/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 12 | UI `admin/alerts/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 13 | UPDATE `layout.tsx` | `frontend-development` | `ui-styling` | `debugging` |
| 14 | Self-verify | `debugging` | `code-review` | `database-admin` |

## Files KHÔNG được đụng (Do Not Touch)
- Phase 5 files: `apps/api/dependencies/admin.py`, `apps/api/services/audit.py`, `supabase/migrations/0022_admin_panel_foundation.sql`.
- Phase 6 files: `apps/api/routers/admin_users.py`, `admin_credit.py`, `admin_pricing.py`, `apps/web/app/(admin)/admin/users/*`, `admin/credits/page.tsx`, 4 web proxy admin.
- User-facing routes (`/api/users/*`, `/api/credits/*`, `/api/assistants/*`, `/api/jobs/*`, `/api/channels/collect`).
- Worker tasks (`apps/worker/tasks/*`).
- Migration 0001-0022 (trừ Phase 5 admin foundation đã apply).

---

## Micro-Steps

### Step 1: Tạo `supabase/migrations/0023_api_provider_keys.sql`
**File:** `supabase/migrations/0023_api_provider_keys.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `backend-development`.
  - **Fallback:** `devops`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0023_api_provider_keys.sql
-- Purpose: API provider key storage (encrypted via app-layer Fernet)
-- ============================================================

CREATE TABLE IF NOT EXISTS api_provider_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,                   -- 'openai', 'gemini', 'cohere', 'elevenlabs', 'youtube', 'pexels', 'pixabay', 'unsplash', 'modal', 'supabase_service_role', 'r2', 'supadata', 'serpapi'
  label TEXT NOT NULL,                      -- 'OpenAI key #1'
  encrypted_value BYTEA NOT NULL,           -- Fernet-encrypted raw value
  is_active BOOLEAN NOT NULL DEFAULT true,
  rate_limit_rpm INT,
  monthly_budget_usd NUMERIC(10,2),
  current_month_cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  last_tested_at TIMESTAMPTZ,
  last_test_status TEXT,                    -- 'ok' | 'fail' | 'timeout'
  last_test_latency_ms INT,
  last_test_error TEXT,
  expires_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  archived_at TIMESTAMPTZ,                  -- Soft archive (giữ value 7 ngày)
  UNIQUE(provider, label)
);

CREATE INDEX IF NOT EXISTS idx_apikeys_provider_active ON api_provider_keys(provider) WHERE is_active AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_apikeys_archived ON api_provider_keys(archived_at) WHERE archived_at IS NOT NULL;

-- RLS: deny non-service, only service_role reads/writes
ALTER TABLE api_provider_keys ENABLE ROW LEVEL SECURITY;
-- (không tạo policy → default deny)
```

**Verify command:**
```powershell
# Apply migration (nếu có Supabase CLI)
supabase db reset
# Hoặc copy SQL chạy qua Dashboard SQL Editor
```

**Expected output:** Migration apply thành công, không break schema cũ.

---

### Step 2: Tạo `supabase/migrations/0024_api_usage_logs.sql`
**File:** `supabase/migrations/0024_api_usage_logs.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `backend-development`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0024_api_usage_logs.sql
-- Purpose: Track API usage + cost per provider key
-- ============================================================

CREATE TABLE IF NOT EXISTS api_usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_key_id UUID NOT NULL REFERENCES api_provider_keys(id) ON DELETE CASCADE,
  feature TEXT,                              -- 'llm_text', 'embedding', 'tts', ...
  success BOOLEAN NOT NULL,
  latency_ms INT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  error_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_key_time ON api_usage_logs(provider_key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_feature_time ON api_usage_logs(feature, created_at DESC);

-- RLS: deny non-service
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

-- View: aggregated cost per provider (24h/7d/30d)
CREATE OR REPLACE VIEW api_usage_summary AS
SELECT
  provider_key_id,
  feature,
  COUNT(*) AS total_calls,
  COUNT(*) FILTER (WHERE success) AS success_calls,
  ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
  SUM(cost_usd) AS total_cost_usd,
  DATE_TRUNC('hour', created_at) AS hour_bucket
FROM api_usage_logs
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY provider_key_id, feature, DATE_TRUNC('hour', created_at);
```

**Verify command:**
```powershell
# Test query view
psql -c "SELECT * FROM api_usage_summary LIMIT 1;"
```
**Expected:** Empty result (chưa có data).

---

### Step 3: Tạo `supabase/migrations/0025_admin_alerts.sql`
**File:** `supabase/migrations/0025_admin_alerts.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `backend-development`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0025_admin_alerts.sql
-- Purpose: Admin alerts (budget/quota/error rate)
-- ============================================================

CREATE TABLE IF NOT EXISTS admin_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
  category TEXT NOT NULL,                -- 'budget', 'quota', 'error_rate', 'security'
  message TEXT NOT NULL,
  context JSONB DEFAULT '{}',
  resolved_at TIMESTAMPTZ,
  resolved_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON admin_alerts(created_at DESC) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON admin_alerts(severity, created_at DESC);

ALTER TABLE admin_alerts ENABLE ROW LEVEL SECURITY;

-- RPC: create_alert (idempotent per category + context hash)
CREATE OR REPLACE FUNCTION create_alert(
  p_severity TEXT,
  p_category TEXT,
  p_message TEXT,
  p_context JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
  v_id UUID;
  v_context_hash TEXT;
BEGIN
  v_context_hash := md5(p_context::text);
  
  -- Idempotent: nếu đã có unresolved alert với cùng category + context_hash → không insert mới
  IF EXISTS (
    SELECT 1 FROM admin_alerts
    WHERE category = p_category
      AND resolved_at IS NULL
      AND md5(context::text) = v_context_hash
      AND created_at > NOW() - INTERVAL '1 hour'
  ) THEN
    SELECT id INTO v_id FROM admin_alerts
    WHERE category = p_category
      AND resolved_at IS NULL
      AND md5(context::text) = v_context_hash
    LIMIT 1;
    RETURN v_id;
  END IF;
  
  INSERT INTO admin_alerts (severity, category, message, context)
  VALUES (p_severity, p_category, p_message, p_context)
  RETURNING id INTO v_id;
  
  RETURN v_id;
END;
$$ LANGUAGE plpgsql;
```

**Verify command:**
```powershell
# Test RPC
psql -c "SELECT create_alert('info', 'budget', 'Test alert', '{}'::jsonb);"
```
**Expected:** Return UUID.

---

### Step 4: Tạo `apps/api/services/vault.py`
**File:** `apps/api/services/vault.py` (NEW)
**Vai trò:** Fernet encryption wrapper.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `devops`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Encryption wrapper — dùng Fernet (AES-128-CBC + HMAC SHA-256).
ENCRYPTION_KEY phải được set trong env (44-char base64).
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """
    Lấy Fernet instance. Key được derive từ ENCRYPTION_KEY env.
    Nếu chưa có → derive từ SECRET_KEY (fallback cho dev).
    """
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Fallback: dùng SECRET_KEY (đã có) làm base, hash SHA-256 → 32 bytes → base64
        secret = os.environ.get('SECRET_KEY', 'dev-fallback-secret-change-me')
        key_bytes = hashlib.sha256(secret.encode()).digest()
        key = base64.urlsafe_b64encode(key_bytes).decode()
    
    return Fernet(key.encode())


def encrypt(plaintext: str) -> bytes:
    """Encrypt string → bytes. Lưu vào BYTEA column."""
    if not plaintext:
        raise ValueError('Cannot encrypt empty value')
    return _get_fernet().encrypt(plaintext.encode())


def decrypt(ciphertext: bytes) -> str:
    """Decrypt bytes → string. Chỉ dùng khi cần gọi provider."""
    if not ciphertext:
        raise ValueError('Cannot decrypt empty value')
    return _get_fernet().decrypt(ciphertext).decode()


def generate_key() -> str:
    """Generate random Fernet key. Tier 2 dùng để tạo ENCRYPTION_KEY mới."""
    return Fernet.generate_key().decode()
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.services.vault import encrypt, decrypt, generate_key; print('vault OK'); k = generate_key(); assert decrypt(encrypt('test')) == 'test'; print('roundtrip OK')"
```

**Expected output:**
```
vault OK
roundtrip OK
```

---

### Step 5: Tạo `apps/api/services/key_resolver.py`
**File:** `apps/api/services/key_resolver.py` (NEW)
**Vai trò:** Lookup active key theo provider, cache 60s, fallback chain.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
python -c "from apps.api.services.key_resolver import resolve_key, invalidate_cache, get_active_keys_summary; print('key_resolver OK')"
```

**Expected output:** `key_resolver OK`.

---

### Step 6: Tạo `apps/api/services/usage_tracker.py`
**File:** `apps/api/services/usage_tracker.py` (NEW)
**Vai trò:** Decorator `@track_usage(provider, feature)` log API call + cost.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
python -c "from apps.api.services.usage_tracker import track_usage; print('usage_tracker OK')"
```

**Expected output:** `usage_tracker OK`.

---

### Step 7: Tạo `apps/api/routers/admin_api_keys.py`
**File:** `apps/api/routers/admin_api_keys.py` (NEW)
**Vai trò:** 7 endpoints (list, create, update, rotate, delete, test, usage).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `database-admin`.

**Code cần viết:**
```python
"""
Admin API Keys Management — 7 endpoints.
Mounted dưới /api/admin/api-keys.
"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.vault import encrypt
from apps.api.services.audit import log_admin_action
from apps.api.services.key_resolver import invalidate_cache


router = APIRouter(prefix="/api/admin/api-keys", tags=["Admin API Keys"])


# --- Schemas ---

class KeyCreate(BaseModel):
    provider: str
    label: str
    value: str
    rate_limit_rpm: Optional[int] = None
    monthly_budget_usd: Optional[float] = None
    expires_at: Optional[str] = None


class KeyUpdate(BaseModel):
    label: Optional[str] = None
    is_active: Optional[bool] = None
    rate_limit_rpm: Optional[int] = None
    monthly_budget_usd: Optional[float] = None
    expires_at: Optional[str] = None


class KeyRotate(BaseModel):
    new_value: str


# --- Test functions per provider ---

def _test_provider(provider: str, plaintext_key: str) -> dict:
    """Test connectivity bằng 1 call nhỏ tới provider."""
    start = time.time()
    try:
        if provider == 'openai':
            from openai import OpenAI
            client = OpenAI(api_key=plaintext_key)
            client.models.list()
        elif provider == 'cohere':
            import cohere
            client = cohere.Client(plaintext_key)
            client.tokenize(text='test', model='embed-multilingual-v3.0')
        elif provider == 'r2':
            import boto3
            from botocore.config import Config
            # Lấy endpoint từ env (R2 multi-key chưa refactor Phase 7)
            client = boto3.client(
                's3',
                endpoint_url=__import__('os').environ.get('R2_ENDPOINT'),
                aws_access_key_id=plaintext_key,
                aws_secret_access_key=__import__('os').environ.get('R2_SECRET_ACCESS_KEY'),
                region_name='auto',
                config=Config(retries={'max_attempts': 1}),
            )
            client.head_bucket(Bucket=__import__('os').environ.get('R2_BUCKET_UPLOADS', 'appdk-uploads'))
        elif provider == 'modal':
            import modal
            # Modal chỉ check token hợp lệ (không gọi function thật)
            modal.config.Config.set_token_id(plaintext_key)
        elif provider in ('supadata', 'serpapi'):
            import requests
            url = f'https://api.supadata.ai/v1/health' if provider == 'supadata' else f'https://serpapi.com/account.json?api_key={plaintext_key}'
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
        elif provider == 'youtube':
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=plaintext_key)
            youtube.channels().list(part='id', id='UC_x5XG1OV2P6uZZ5FSM9Ttw').execute()  # Google channel
        elif provider == 'supabase_service_role':
            from supabase import create_client
            client = create_client(
                __import__('os').environ.get('SUPABASE_URL'),
                plaintext_key,
            )
            # Test bằng cách list 1 row
            client.table('users').select('id').limit(1).execute()
        else:
            return {'ok': False, 'latency_ms': 0, 'error': f'Unknown provider {provider}', 'status': 'fail'}
        
        latency_ms = int((time.time() - start) * 1000)
        return {'ok': True, 'latency_ms': latency_ms, 'error': None, 'status': 'ok'}
    
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {'ok': False, 'latency_ms': latency_ms, 'error': str(e)[:200], 'status': 'fail'}


# --- Endpoints ---

@router.get("")
async def list_keys(
    admin_id: str = Depends(require_admin),
    provider: Optional[str] = None,
    include_archived: bool = False,
):
    """List api_provider_keys (không trả encrypted_value)."""
    db = get_supabase_admin()
    query = db.table('api_provider_keys').select('id, provider, label, is_active, rate_limit_rpm, monthly_budget_usd, current_month_cost_usd, last_used_at, last_tested_at, last_test_status, last_test_latency_ms, expires_at, archived_at, created_at')
    
    if provider:
        query = query.eq('provider', provider)
    if not include_archived:
        query = query.is_('archived_at', 'null')
    
    result = query.order('provider, created_at', desc=True).execute()
    return result.data or []


@router.post("")
async def create_key(
    payload: KeyCreate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Create key + encrypt + insert."""
    db = get_supabase_admin()
    
    encrypted = encrypt(payload.value)
    
    db.table('api_provider_keys').insert({
        'provider': payload.provider,
        'label': payload.label,
        'encrypted_value': encrypted.hex(),  # BYTEA nhận hex string
        'is_active': True,
        'rate_limit_rpm': payload.rate_limit_rpm,
        'monthly_budget_usd': payload.monthly_budget_usd,
        'expires_at': payload.expires_at,
        'created_by': admin_id,
    }).execute()
    
    invalidate_cache(payload.provider)
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='api_key.create',
        target_type='api_key',
        target_id=f'{payload.provider}/{payload.label}',
        after={'provider': payload.provider, 'label': payload.label},
        reason=f'Created key for {payload.provider}',
        ip=request.client.host if request.client else None,
    )
    
    return {'provider': payload.provider, 'label': payload.label, 'status': 'created'}


@router.patch("/{key_id}")
async def update_key(
    key_id: str,
    update: KeyUpdate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Update metadata (không đổi encrypted_value)."""
    db = get_supabase_admin()
    
    before = db.table('api_provider_keys').select('*').eq('id', key_id).single().execute().data
    if not before:
        raise HTTPException(404, 'Key not found')
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    update_data['updated_at'] = 'now()'
    
    db.table('api_provider_keys').update(update_data).eq('id', key_id).execute()
    after = db.table('api_provider_keys').select('*').eq('id', key_id).single().execute().data
    
    if 'is_active' in update_data:
        invalidate_cache(before['provider'])
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='api_key.update',
        target_type='api_key',
        target_id=key_id,
        before={'provider': before['provider'], 'is_active': before['is_active']},
        after={'provider': after['provider'], 'is_active': after['is_active']},
        ip=request.client.host if request.client else None,
    )
    
    return after


@router.post("/{key_id}/rotate")
async def rotate_key(
    key_id: str,
    payload: KeyRotate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Rotate: archive old (giữ 7 ngày) + insert new + invalidate cache."""
    db = get_supabase_admin()
    
    before = db.table('api_provider_keys').select('*').eq('id', key_id).single().execute().data
    if not before:
        raise HTTPException(404, 'Key not found')
    
    # 1) Archive old (set archived_at)
    db.table('api_provider_keys').update({
        'archived_at': 'now()',
        'is_active': False,
        'updated_at': 'now()',
    }).eq('id', key_id).execute()
    
    # 2) Insert new (same provider + label, new encrypted value)
    new_encrypted = encrypt(payload.new_value)
    new_row = db.table('api_provider_keys').insert({
        'provider': before['provider'],
        'label': before['label'],
        'encrypted_value': new_encrypted.hex(),
        'is_active': True,
        'rate_limit_rpm': before.get('rate_limit_rpm'),
        'monthly_budget_usd': before.get('monthly_budget_usd'),
        'created_by': admin_id,
    }).execute()
    
    invalidate_cache(before['provider'])
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='api_key.rotate',
        target_type='api_key',
        target_id=key_id,
        before={'provider': before['provider'], 'label': before['label']},
        after={'provider': before['provider'], 'label': before['label'], 'new_id': new_row.data[0]['id'] if new_row.data else None},
        reason='Rotated API key',
        ip=request.client.host if request.client else None,
    )
    
    return {'status': 'rotated', 'archived_id': key_id, 'new_id': new_row.data[0]['id'] if new_row.data else None}


@router.delete("/{key_id}")
async def archive_key(
    key_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Soft archive (set archived_at). Hard delete Phase 9+."""
    db = get_supabase_admin()
    
    before = db.table('api_provider_keys').select('provider').eq('id', key_id).single().execute().data
    if not before:
        raise HTTPException(404, 'Key not found')
    
    db.table('api_provider_keys').update({
        'archived_at': 'now()',
        'is_active': False,
        'updated_at': 'now()',
    }).eq('id', key_id).execute()
    
    invalidate_cache(before['provider'])
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='api_key.archive',
        target_type='api_key',
        target_id=key_id,
        ip=request.client.host if request.client else None,
    )
    
    return None


@router.post("/{key_id}/test")
async def test_key(
    key_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Test connectivity — decrypt + ping provider."""
    db = get_supabase_admin()
    
    row = db.table('api_provider_keys').select('*').eq('id', key_id).single().execute().data
    if not row:
        raise HTTPException(404, 'Key not found')
    
    # Decrypt
    from apps.api.services.vault import decrypt
    plaintext = decrypt(bytes.fromhex(row['encrypted_value']))
    
    # Test
    result = _test_provider(row['provider'], plaintext)
    
    # Update last_test_*
    db.table('api_provider_keys').update({
        'last_tested_at': datetime.now(timezone.utc).isoformat(),
        'last_test_status': result['status'],
        'last_test_latency_ms': result['latency_ms'],
        'last_test_error': result['error'],
        'updated_at': 'now()',
    }).eq('id', key_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='api_key.test',
        target_type='api_key',
        target_id=key_id,
        after={'status': result['status'], 'latency_ms': result['latency_ms']},
        ip=request.client.host if request.client else None,
    )
    
    return result


@router.get("/{key_id}/usage")
async def get_key_usage(
    key_id: str,
    admin_id: str = Depends(require_admin),
    window: str = '7d',  # '24h' | '7d' | '30d'
):
    """Usage 24h/7d/30d."""
    db = get_supabase_admin()
    
    window_map = {'24h': '1 day', '7d': '7 days', '30d': '30 days'}
    interval = window_map.get(window, '7 days')
    
    result = db.table('api_usage_logs').select('*').eq('provider_key_id', key_id).gte('created_at', f'now() - interval \'{interval}\'').order('created_at', desc=True).limit(1000).execute()
    
    logs = result.data or []
    
    total_calls = len(logs)
    success_calls = sum(1 for l in logs if l['success'])
    avg_latency = sum(l['latency_ms'] for l in logs) / total_calls if total_calls > 0 else 0
    total_cost = sum(l['cost_usd'] for l in logs if l['success'])
    
    return {
        'window': window,
        'total_calls': total_calls,
        'success_calls': success_calls,
        'success_rate': round(success_calls / total_calls, 3) if total_calls > 0 else 0,
        'avg_latency_ms': round(avg_latency, 2),
        'total_cost_usd': round(total_cost, 6),
    }
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_api_keys import router; print('admin_api_keys OK')"
```

**Expected output:** `admin_api_keys OK`.

---

### Step 8: Tạo `apps/api/routers/admin_alerts.py`
**File:** `apps/api/routers/admin_alerts.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Admin Alerts Management — 2 endpoints.
Mounted dưới /api/admin/alerts.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action


router = APIRouter(prefix="/api/admin/alerts", tags=["Admin Alerts"])


@router.get("")
async def list_alerts(
    admin_id: str = Depends(require_admin),
    severity: Optional[str] = None,
    category: Optional[str] = None,
    include_resolved: bool = False,
    limit: int = 100,
):
    """List admin_alerts. Default: unresolved only."""
    db = get_supabase_admin()
    query = db.table('admin_alerts').select('*')
    
    if not include_resolved:
        query = query.is_('resolved_at', 'null')
    if severity:
        query = query.eq('severity', severity)
    if category:
        query = query.eq('category', category)
    
    result = query.order('created_at', desc=True).limit(limit).execute()
    return result.data or []


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Resolve alert."""
    db = get_supabase_admin()
    
    before = db.table('admin_alerts').select('*').eq('id', alert_id).single().execute().data
    if not before:
        raise HTTPException(404, 'Alert not found')
    if before.get('resolved_at'):
        raise HTTPException(400, 'Alert already resolved')
    
    db.table('admin_alerts').update({
        'resolved_at': 'now()',
        'resolved_by': admin_id,
    }).eq('id', alert_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='alert.resolve',
        target_type='alert',
        target_id=alert_id,
        before={'category': before.get('category'), 'severity': before.get('severity')},
        ip=request.client.host if request.client else None,
    )
    
    return {'id': alert_id, 'resolved': True}
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_alerts import router; print('admin_alerts OK')"
```

**Expected output:** `admin_alerts OK`.

---

### Step 9: UPDATE `apps/api/main.py` mount 2 routers
**File:** `apps/api/main.py` (UPDATE)
**Vị trí:** Sau Phase 6 admin imports.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** Phase 6 admin imports, **THÊM:**
```python
from apps.api.routers.admin_api_keys import router as admin_api_keys_router
from apps.api.routers.admin_alerts import router as admin_alerts_router
```

**SAU** Phase 6 admin mounts, **THÊM:**
```python
app.include_router(admin_api_keys_router)
app.include_router(admin_alerts_router)
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path]); print(len(routes), 'admin routes'); [print(r) for r in routes if 'api-keys' in r or 'alerts' in r]"
```

**Expected output:** ≥ 9 routes mới (7 api-keys + 2 alerts).

---

### Step 10: Tạo 5 web proxy routes
**Files (5 NEW):**
- `apps/web/app/api/admin/api-keys/route.ts`
- `apps/web/app/api/admin/api-keys/[id]/route.ts`
- `apps/web/app/api/admin/api-keys/[id]/test/route.ts`
- `apps/web/app/api/admin/api-keys/[id]/rotate/route.ts`
- `apps/web/app/api/admin/alerts/route.ts`
- `apps/web/app/api/admin/alerts/[id]/resolve/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Pattern (lặp lại cho mỗi route):**

**`apps/web/app/api/admin/api-keys/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/api-keys${params ? `?${params}` : ''}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json();
  try {
    const response = await apiFetch('/api/admin/api-keys', {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/api-keys/[id]/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  const body = await req.json();
  try {
    const response = await apiFetch(`/api/admin/api-keys/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  try {
    const response = await apiFetch(`/api/admin/api-keys/${id}`, { method: 'DELETE' }, token);
    return NextResponse.json(null, { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/api-keys/[id]/test/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  try {
    const response = await apiFetch(`/api/admin/api-keys/${id}/test`, { method: 'POST' }, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/api-keys/[id]/rotate/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  const body = await req.json();
  try {
    const response = await apiFetch(`/api/admin/api-keys/${id}/rotate`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/alerts/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/alerts${params ? `?${params}` : ''}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/alerts/[id]/resolve/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { id } = await params;
  try {
    const response = await apiFetch(`/api/admin/alerts/${id}/resolve`, { method: 'POST' }, token);
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

### Step 11: Tạo `apps/web/app/(admin)/admin/api-keys/page.tsx`
**File:** `apps/web/app/(admin)/admin/api-keys/page.tsx` (NEW)
**Vai trò:** Provider table + form create.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

interface ApiKey {
  id: string;
  provider: string;
  label: string;
  is_active: boolean;
  rate_limit_rpm: number | null;
  monthly_budget_usd: number | null;
  current_month_cost_usd: number;
  last_tested_at: string | null;
  last_test_status: string | null;
  last_test_latency_ms: number | null;
  expires_at: string | null;
  archived_at: string | null;
  created_at: string;
}

export default function AdminApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [formProvider, setFormProvider] = useState('openai');
  const [formLabel, setFormLabel] = useState('');
  const [formValue, setFormValue] = useState('');
  const [formBudget, setFormBudget] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadKeys();
  }, []);

  function loadKeys() {
    setLoading(true);
    fetch('/api/admin/api-keys')
      .then((r) => r.json())
      .then(setKeys)
      .finally(() => setLoading(false));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setMessage('');
    const res = await fetch('/api/admin/api-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: formProvider,
        label: formLabel,
        value: formValue,
        monthly_budget_usd: formBudget ? Number(formBudget) : null,
      }),
    });
    if (res.ok) {
      setMessage('✓ Created');
      setShowCreate(false);
      setFormLabel(''); setFormValue(''); setFormBudget('');
      loadKeys();
    } else {
      const err = await res.json();
      setMessage(`Error: ${err.detail || 'unknown'}`);
    }
    setCreating(false);
  }

  async function handleTest(id: string) {
    setMessage('');
    const res = await fetch(`/api/admin/api-keys/${id}/test`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      setMessage(`✓ Test OK (${data.latency_ms}ms)`);
    } else {
      setMessage(`✗ Test failed: ${data.error}`);
    }
    loadKeys();
  }

  async function handleRotate(id: string, label: string) {
    const newValue = prompt(`New value for ${label}:`);
    if (!newValue) return;
    const res = await fetch(`/api/admin/api-keys/${id}/rotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_value: newValue }),
    });
    if (res.ok) {
      setMessage('✓ Rotated');
      loadKeys();
    } else {
      setMessage('✗ Rotate failed');
    }
  }

  // Group by provider
  const byProvider = keys.reduce((acc, k) => {
    acc[k.provider] = acc[k.provider] || [];
    acc[k.provider].push(k);
    return acc;
  }, {} as Record<string, ApiKey[]>);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">API Keys</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{keys.length} keys total</p>
      </div>

      {message && <div className="glass rounded-xl p-3 text-sm">{message}</div>}

      <button
        onClick={() => setShowCreate(!showCreate)}
        className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold"
      >
        {showCreate ? 'Cancel' : '+ Add Key'}
      </button>

      {showCreate && (
        <form onSubmit={handleCreate} className="glass rounded-2xl p-5 space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <select value={formProvider} onChange={(e) => setFormProvider(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white">
              {['openai', 'cohere', 'modal', 'r2', 'supadata', 'serpapi', 'youtube', 'elevenlabs', 'pexels', 'pixabay', 'unsplash', 'supabase_service_role'].map(p =>
                <option key={p} value={p}>{p}</option>
              )}
            </select>
            <input type="text" value={formLabel} onChange={(e) => setFormLabel(e.target.value)} required
              placeholder="Label (e.g. 'OpenAI key #1')"
              className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]" />
          </div>
          <input type="password" value={formValue} onChange={(e) => setFormValue(e.target.value)} required
            placeholder="API key value (sẽ được encrypt)"
            className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]" />
          <input type="number" step="0.01" value={formBudget} onChange={(e) => setFormBudget(e.target.value)}
            placeholder="Monthly budget USD (optional)"
            className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]" />
          <button type="submit" disabled={creating}
            className="w-full px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-50">
            {creating ? 'Encrypting…' : 'Create + Encrypt'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="text-center text-[var(--fg-tertiary)] py-12">Loading…</div>
      ) : Object.keys(byProvider).length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center text-[var(--fg-tertiary)]">No keys</div>
      ) : (
        Object.entries(byProvider).map(([provider, pkeys]) => (
          <div key={provider} className="glass rounded-2xl overflow-hidden">
            <div className="px-5 py-3 bg-[var(--surface)] border-b border-[var(--glass-border)]">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--fg-tertiary)]">
                {provider} · {pkeys.length} key{pkeys.length !== 1 ? 's' : ''}
              </h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
                <tr>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Label</th>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Status</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Budget</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Cost (mo)</th>
                  <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Last test</th>
                  <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pkeys.map((k) => (
                  <tr key={k.id} className="border-b border-[var(--glass-border)]">
                    <td className="px-4 py-3 text-white">{k.label}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                        !k.is_active ? 'bg-gray-500/20 text-gray-400' :
                        k.archived_at ? 'bg-red-500/20 text-red-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {k.archived_at ? 'archived' : k.is_active ? 'active' : 'inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {k.monthly_budget_usd ? `$${k.monthly_budget_usd}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      ${(k.current_month_cost_usd || 0).toFixed(4)}
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                      {k.last_test_status ? (
                        <span className={k.last_test_status === 'ok' ? 'text-green-400' : 'text-red-400'}>
                          {k.last_test_status} · {k.last_test_latency_ms}ms
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={() => handleTest(k.id)}
                        className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">
                        Test
                      </button>
                      <button onClick={() => handleRotate(k.id, k.label)}
                        className="text-xs px-2 py-1 rounded bg-orange-500/20 text-orange-400">
                        Rotate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
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

### Step 12: Tạo `apps/web/app/(admin)/admin/alerts/page.tsx`
**File:** `apps/web/app/(admin)/admin/alerts/page.tsx` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  category: string;
  message: string;
  context: Record<string, any>;
  resolved_at: string | null;
  created_at: string;
}

export default function AdminAlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showResolved, setShowResolved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();
  }, [showResolved]);

  function loadAlerts() {
    setLoading(true);
    fetch(`/api/admin/alerts?include_resolved=${showResolved}`)
      .then((r) => r.json())
      .then(setAlerts)
      .finally(() => setLoading(false));
  }

  async function handleResolve(id: string) {
    await fetch(`/api/admin/alerts/${id}/resolve`, { method: 'POST' });
    loadAlerts();
  }

  const severityColor = (s: string) =>
    s === 'critical' ? 'bg-red-500/20 text-red-400' :
    s === 'warning' ? 'bg-orange-500/20 text-orange-400' :
    'bg-blue-500/20 text-blue-400';

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Alerts</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{alerts.filter(a => !a.resolved_at).length} unresolved</p>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={showResolved} onChange={(e) => setShowResolved(e.target.checked)}
          className="rounded" />
        <span>Show resolved</span>
      </label>

      {loading ? (
        <div className="text-center text-[var(--fg-tertiary)] py-12">Loading…</div>
      ) : alerts.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center text-[var(--fg-tertiary)]">
          No alerts 🎉
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.id} className={`glass rounded-2xl p-5 ${a.resolved_at ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${severityColor(a.severity)}`}>
                      {a.severity}
                    </span>
                    <span className="text-xs text-[var(--fg-tertiary)]">{a.category}</span>
                    <span className="text-xs text-[var(--fg-tertiary)]">
                      {new Date(a.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                  <p className="text-sm">{a.message}</p>
                  {Object.keys(a.context).length > 0 && (
                    <pre className="text-xs text-[var(--fg-tertiary)] bg-[var(--surface)] rounded p-2 overflow-x-auto">
                      {JSON.stringify(a.context, null, 2)}
                    </pre>
                  )}
                  {a.resolved_at && (
                    <p className="text-xs text-green-400">
                      ✓ Resolved {new Date(a.resolved_at).toLocaleString('vi-VN')}
                    </p>
                  )}
                </div>
                {!a.resolved_at && (
                  <button
                    onClick={() => handleResolve(a.id)}
                    className="px-3 py-1 rounded-lg bg-green-500/20 text-green-400 text-sm font-semibold shrink-0"
                  >
                    Resolve
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
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

### Step 13: UPDATE `apps/web/app/(admin)/layout.tsx` enable API Keys + Alerts
**File:** `apps/web/app/(admin)/layout.tsx` (UPDATE)
**Vị trí:** Line 12 (API Keys) + line 14 (Alerts).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Code cần viết (2 lần `StrReplace`):**

**Thay 1 — line 12:**
```typescript
  { href: '/admin/api-keys', label: 'API Keys', icon: IconShield, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/api-keys', label: 'API Keys', icon: IconShield, enabled: true },
```

**Thay 2 — line 14:**
```typescript
  { href: '/admin/alerts', label: 'Alerts', icon: IconAlert, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/alerts', label: 'Alerts', icon: IconAlert, enabled: true },
```

**KHÔNG được sửa:**
- 4 mục còn lại (Pricing, Routing, Audit Logs — Phase 6 chưa enable Users/Credits cũng chưa đụng).
- Layout structure.

**Verify command:**
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "enabled:" | Measure-Object -Line
```

**Expected output:** 8 lines.

---

### Step 14: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `database-admin`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) Cryptography installed
pip show cryptography 2>&1 | Select-String "Name|Version"

# 2) All Python imports
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.vault import encrypt, decrypt, generate_key; print('vault OK')"
python -c "from apps.api.services.key_resolver import resolve_key, invalidate_cache, get_active_keys_summary; print('key_resolver OK')"
python -c "from apps.api.services.usage_tracker import track_usage; print('usage_tracker OK')"
python -c "from apps.api.routers.admin_api_keys import router; print('admin_api_keys OK')"
python -c "from apps.api.routers.admin_alerts import router; print('admin_alerts OK')"

# 3) Admin routes count
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and ('api-keys' in r.path or 'alerts' in r.path)]; print(len(routes), 'new routes'); [print(r) for r in sorted(routes)]"

# 4) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 5) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 6) 3 migration files tồn tại
Test-Path "..\supabase\migrations\0023_api_provider_keys.sql"
Test-Path "..\supabase\migrations\0024_api_usage_logs.sql"
Test-Path "..\supabase\migrations\0025_admin_alerts.sql"

# 7) 2 trang admin tồn tại
Test-Path "app\(admin)\admin\api-keys\page.tsx"
Test-Path "app\(admin)\admin\alerts\page.tsx"
```

**Expected output:**
- cryptography installed
- 6 dòng "OK"
- 9 new routes (7 api-keys + 2 alerts)
- 2 tests PASSED
- 0 errors TS
- 3 file SQL = True
- 2 file TSX = True

---

## Definition of Done cho Phase này
- 3 migrations mới apply thành công (Phase 7 schema).
- `vault.py` (Fernet AES) + `key_resolver.py` (cache 60s) + `usage_tracker.py` (decorator) services.
- 2 routers admin mới (`admin_api_keys` với 7 endpoints + `admin_alerts` với 2 endpoints).
- 6 web proxy routes mới.
- 2 trang admin mới (`/admin/api-keys` + `/admin/alerts`).
- Sidebar enable API Keys + Alerts.
- TS compile 0 errors.
- Existing pytest PASSED.
- `cryptography` library installed.
- Test rotate key KHÔNG break TTS route (worker vẫn dùng env — Phase 8+ refactor).
- KHÔNG file nào trong Phase 5/6 bị đụng.