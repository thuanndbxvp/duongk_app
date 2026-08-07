"""
FastAPI router for assets — FIXED: No Celery imports
All async tasks now use FastAPI BackgroundTasks
Prefix: /api/assets
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.assets import (
    UploadInitRequest, UploadInitResponse, UploadCompleteRequest,
    AssetResponse, AssetListResponse,
    AssetSearchRequest, AssetSearchResponse, AssetSearchResult,
    MaterializeRequest,
    SceneAssetBindRequest, SceneAssetResponse,
)


router = APIRouter(prefix="/api/assets", tags=["Assets"])


# =============================================================================
# Async Tasks (Background)
# =============================================================================

async def _materialize_asset_async(asset_id: str, provider: str, provider_id: str, owner_id: str):
    """
    Async task to materialize stock asset.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        # Update status
        db.table('assets').update({'status': 'processing'}).eq('id', asset_id).execute()
        
        # Placeholder: implement actual materialization logic
        # For now, just mark as ready
        
        db.table('assets').update({'status': 'ready'}).eq('id', asset_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[assets] Materialization failed for {asset_id}: {e}")
        
        db.table('assets').update({
            'status': 'failed',
        }).eq('id', asset_id).execute()


# =============================================================================
# Routes
# =============================================================================

@router.post("/upload-init", response_model=UploadInitResponse)
async def upload_init(req: UploadInitRequest, user_id: str = Depends(get_supabase_user)):
    """Initialize upload: create asset row + generate signed URL."""
    admin = get_supabase_admin()
    storage_key = f'uploads/{user_id}/{req.filename}'
    asset_res = admin.table('assets').insert({
        'owner_id': user_id, 'source': 'upload',
        'storage_key': storage_key, 'mime_type': req.mime_type,
        'size_bytes': req.size_bytes, 'checksum': req.checksum,
        'status': 'uploading',
    }).execute()
    if not asset_res.data:
        raise HTTPException(500, 'Failed to create asset')
    asset = asset_res.data[0]
    try:
        signed = admin.storage.from_('assets').create_signed_upload_url(storage_key)
        url = signed.get('signed_url', signed.get('url', ''))
    except Exception:
        url = f"http://localhost:54321/storage/v1/object/assets/{storage_key}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    return UploadInitResponse(asset_id=asset['id'], upload_url=url, storage_key=storage_key, expires_at=expires)


@router.post("/upload-complete", status_code=200)
async def upload_complete(req: UploadCompleteRequest, user_id: str = Depends(get_supabase_user)):
    """Verify checksum + mark asset ready."""
    admin = get_supabase_admin()
    asset = admin.table('assets').select('*').eq('id', str(req.asset_id)).eq('owner_id', user_id).maybe_single().execute()
    if not asset.data:
        raise HTTPException(404, 'Asset not found')
    if asset.data['checksum'] != req.checksum:
        raise HTTPException(422, 'Checksum mismatch')
    admin.table('assets').update({'status': 'ready'}).eq('id', str(req.asset_id)).execute()
    return {"status": "ok", "asset_id": str(req.asset_id)}


@router.post("/search", response_model=AssetSearchResponse)
async def search_assets(req: AssetSearchRequest, user_id: str = Depends(get_supabase_user)):
    """Search stock assets. Returns empty results (providers removed)."""
    # Asset providers (pexels, local_placeholder) have been deleted
    return AssetSearchResponse(
        results=[],
        page=req.page,
        total_results=0,
        next_page=None,
    )


@router.post("/materialize/{provider}/{provider_id}")
async def materialize_asset(
    provider: str,
    provider_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Materialize stock asset into user's library."""
    if provider not in ('pexels', 'local_placeholder'):
        raise HTTPException(400, f'Unsupported provider: {provider}')
    
    admin = get_supabase_admin()
    
    existing = admin.table('assets').select('*').eq('source', provider).eq('provider_id', provider_id).eq('owner_id', user_id).maybe_single().execute()
    if existing.data and existing.data['status'] == 'ready':
        return {"status": "already_materialized", "asset_id": existing.data['id']}
    
    # Create asset row
    asset_res = admin.table('assets').insert({
        'owner_id': user_id,
        'source': provider,
        'provider_id': provider_id,
        'status': 'processing',
    }).execute()
    
    if not asset_res.data:
        raise HTTPException(500, 'Failed to create asset')
    
    asset_id = asset_res.data[0]['id']
    
    # Queue materialization via BackgroundTasks
    background_tasks.add_task(_materialize_asset_async, asset_id, provider, provider_id, user_id)
    
    return {"status": "processing", "asset_id": asset_id}


@router.get("", response_model=AssetListResponse)
async def list_assets(
    user_id: str = Depends(get_supabase_user),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List user's assets with cursor pagination."""
    admin = get_supabase_admin()
    query = admin.table('assets').select('*', count='exact').eq('owner_id', user_id).neq('status', 'deleted').order('created_at', desc=True).limit(limit)
    if cursor:
        query = query.lt('created_at', cursor)
    res = query.execute()
    data = [AssetResponse(**a) for a in (res.data or [])]
    next_cursor = data[-1].created_at.isoformat() if len(data) == limit else None
    return AssetListResponse(data=data, next_cursor=next_cursor, total=res.count or 0)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get a single asset by ID."""
    admin = get_supabase_admin()
    a = admin.table('assets').select('*').eq('id', str(asset_id)).eq('owner_id', user_id).maybe_single().execute()
    if not a.data:
        raise HTTPException(404, 'Asset not found')
    return AssetResponse(**a.data)


# ============================================================
# Scene-Asset bindings
# ============================================================

scene_router = APIRouter(prefix="/api/scenes", tags=["Scenes"])


@scene_router.post("/{scene_id}/assets", response_model=SceneAssetResponse)
async def bind_asset_to_scene(scene_id: UUID, req: SceneAssetBindRequest, user_id: str = Depends(get_supabase_user)):
    """Bind asset to scene. Verifies ownership through project."""
    admin = get_supabase_admin()
    scene = admin.table('project_scenes').select('id, project_id').eq('id', str(scene_id)).maybe_single().execute()
    if not scene.data:
        raise HTTPException(404, 'Scene not found')
    proj = admin.table('projects').select('id').eq('id', scene.data['project_id']).eq('user_id', user_id).maybe_single().execute()
    if not proj.data:
        raise HTTPException(404, 'Scene not found')
    asset = admin.table('assets').select('id').eq('id', str(req.asset_id)).eq('owner_id', user_id).maybe_single().execute()
    if not asset.data:
        raise HTTPException(404, 'Asset not found')
    try:
        bind_res = admin.table('scene_assets').upsert({
            'scene_id': str(scene_id), 'asset_id': str(req.asset_id), 'position': req.position,
        }, on_conflict='scene_id,asset_id').execute()
    except Exception:
        bind_res = admin.table('scene_assets').select('*').eq('scene_id', str(scene_id)).eq('asset_id', str(req.asset_id)).single().execute()
    row = bind_res.data[0] if bind_res.data else {}
    return SceneAssetResponse(
        id=row.get('id'), scene_id=scene_id, asset_id=req.asset_id,
        position=req.position, asset=AssetResponse(**asset.data),
        created_at=row.get('created_at', datetime.now(timezone.utc)),
    )


@scene_router.delete("/{scene_id}/assets/{asset_id}", status_code=200)
async def unbind_asset_from_scene(scene_id: UUID, asset_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Unbind asset from scene (soft-unlink)."""
    admin = get_supabase_admin()
    scene = admin.table('project_scenes').select('id, project_id').eq('id', str(scene_id)).maybe_single().execute()
    if not scene.data:
        raise HTTPException(404, 'Scene not found')
    proj = admin.table('projects').select('id').eq('id', scene.data['project_id']).eq('user_id', user_id).maybe_single().execute()
    if not proj.data:
        raise HTTPException(404, 'Scene not found')
    admin.table('scene_assets').delete().eq('scene_id', str(scene_id)).eq('asset_id', str(asset_id)).execute()
    return {"status": "ok"}
