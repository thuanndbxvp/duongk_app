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