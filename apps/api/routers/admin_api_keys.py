"""
Admin API Keys Management — 7 endpoints.
Mounted dưới /api/admin/api-keys.
"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from apps.api.dependencies.admin import require_admin, require_mfa_for_critical
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.vault import encrypt
from apps.api.services.audit import log_admin_action
from apps.api.services.key_resolver import invalidate_cache


router = APIRouter(prefix="/api/admin/api-keys", tags=["Admin API Keys"])


# --- Provider whitelist ---
# Must sync với apps/web/app/(admin)/admin/api-keys/page.tsx dropdown
# với supabase/migrations/0023_api_provider_keys.sql column comment
ALLOWED_PROVIDERS = frozenset({
    'openai',                  # GPT-4o, Whisper, TTS
    'gemini',                  # Gemini Pro, Vision
    'cohere',                  # Embed v3
    'elevenlabs',              # TTS premium
    'youtube',                 # YouTube Data API v3
    'pexels',                  # Footage search
    'pixabay',                 # Footage search
    'unsplash',                # Footage search
    'modal',                   # Modal GPU workers
    'supabase_service_role',   # Service role key
    'r2',                      # Cloudflare R2
    'supadata',                # Transcript (Tier 2)
    'serpapi',                 # Niche validation fallback
    'groq',                    # Groq Whisper ASR (Tier 3a — main)
})


# --- Schemas ---

class KeyCreate(BaseModel):
    provider: str
    label: str
    value: str
    rate_limit_rpm: Optional[int] = None
    monthly_budget_usd: Optional[float] = None
    expires_at: Optional[str] = None

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_PROVIDERS:
            raise ValueError(
                f'Unknown provider "{v}". Allowed: {sorted(ALLOWED_PROVIDERS)}'
            )
        return v


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
            modal.config.Config.set_token_id(plaintext_key)
        elif provider in ('supadata', 'serpapi'):
            import requests
            url = f'https://api.supadata.ai/v1/health' if provider == 'supadata' else f'https://serpapi.com/account.json?api_key={plaintext_key}'
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
        elif provider == 'youtube':
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=plaintext_key)
            youtube.channels().list(part='id', id='UC_x5XG1OV2P6uZZ5FSM9Ttw').execute()
        elif provider == 'supabase_service_role':
            from supabase import create_client
            client = create_client(
                __import__('os').environ.get('SUPABASE_URL'),
                plaintext_key,
            )
            client.table('users').select('id').limit(1).execute()
        elif provider == 'groq':
            # Groq uses OpenAI-compatible endpoint; ping models list
            import openai
            client = openai.OpenAI(
                api_key=plaintext_key,
                base_url='https://api.groq.com/openai/v1'
            )
            client.models.list()
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
        'encrypted_value': encrypted.hex(),
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
    window: str = '7d',
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