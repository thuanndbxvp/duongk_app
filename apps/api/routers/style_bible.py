"""
FastAPI router for style bible — Phase 09.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.style_bible import (
    StyleBibleCreate, StyleBibleUpdate, StyleBibleResponse,
    StyleBibleApplyRequest, CharacterRef, BackgroundRef,
)

router = APIRouter(prefix="/api/style-bibles", tags=["StyleBible"])


@router.post("", response_model=StyleBibleResponse, status_code=201)
async def create_bible(req: StyleBibleCreate, user_id: str = Depends(get_supabase_user)):
    """Create a new style bible."""
    admin = get_supabase_admin()
    res = admin.table('style_bibles').insert({
        'owner_id': user_id, 'name': req.name, 'description': req.description,
        'visual_palette': req.visual_palette, 'lens_preference': req.lens_preference,
        'motion_style': req.motion_style, 'negative_prompt': req.negative_prompt,
        'version': 1,
    }).execute()
    if not res.data:
        raise HTTPException(500, 'Failed to create')
    bible = res.data[0]
    # Save version snapshot
    admin.table('style_bible_versions').insert({
        'bible_id': bible['id'], 'version': 1,
        'snapshot': {k: str(v) if isinstance(v, UUID) else v for k, v in bible.items()},
    }).execute()
    return StyleBibleResponse(**bible)


@router.get("", response_model=list[StyleBibleResponse])
async def list_bibles(user_id: str = Depends(get_supabase_user)):
    """List user's style bibles."""
    admin = get_supabase_admin()
    res = admin.table('style_bibles').select('*').eq('owner_id', user_id).order('created_at', desc=True).execute()
    return [StyleBibleResponse(**b) for b in (res.data or [])]


@router.get("/{bible_id}", response_model=StyleBibleResponse)
async def get_bible(bible_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get a single style bible."""
    admin = get_supabase_admin()
    b = admin.table('style_bibles').select('*').eq('id', str(bible_id)).eq('owner_id', user_id).maybe_single().execute()
    if not b.data:
        raise HTTPException(404, 'Not found')
    return StyleBibleResponse(**b.data)


@router.patch("/{bible_id}", response_model=StyleBibleResponse)
async def update_bible(bible_id: UUID, req: StyleBibleUpdate, user_id: str = Depends(get_supabase_user)):
    """Update a style bible (auto-version bump)."""
    admin = get_supabase_admin()
    current = admin.table('style_bibles').select('*').eq('id', str(bible_id)).eq('owner_id', user_id).single().execute()
    if not current.data:
        raise HTTPException(404, 'Not found')

    update = {k: v for k, v in req.model_dump(exclude_none=True).items()}
    new_ver = current.data['version'] + 1
    update['version'] = new_ver

    admin.table('style_bibles').update(update).eq('id', str(bible_id)).execute()
    updated = admin.table('style_bibles').select('*').eq('id', str(bible_id)).single().execute()

    # Save version snapshot
    admin.table('style_bible_versions').insert({
        'bible_id': str(bible_id), 'version': new_ver,
        'snapshot': {k: str(v) if isinstance(v, UUID) else v for k, v in updated.data.items()},
    }).execute()

    return StyleBibleResponse(**updated.data)


@router.post("/{bible_id}/rollback/{version}")
async def rollback_bible(bible_id: UUID, version: int, user_id: str = Depends(get_supabase_user)):
    """Rollback to a previous version."""
    admin = get_supabase_admin()
    current = admin.table('style_bibles').select('*').eq('id', str(bible_id)).eq('owner_id', user_id).single().execute()
    if not current.data:
        raise HTTPException(404, 'Not found')

    snap = admin.table('style_bible_versions').select('*').eq('bible_id', str(bible_id)).eq('version', version).single().execute()
    if not snap.data:
        raise HTTPException(404, 'Version not found')

    snapshot = snap.data['snapshot']
    new_ver = current.data['version'] + 1
    admin.table('style_bibles').update({
        'name': snapshot.get('name', current.data['name']),
        'description': snapshot.get('description', ''),
        'visual_palette': snapshot.get('visual_palette', {}),
        'lens_preference': snapshot.get('lens_preference', ''),
        'motion_style': snapshot.get('motion_style', ''),
        'negative_prompt': snapshot.get('negative_prompt', ''),
        'version': new_ver,
    }).eq('id', str(bible_id)).execute()

    return {"status": "rolled_back", "from_version": version, "new_version": new_ver}


@router.post("/{bible_id}/assets")
async def add_asset_ref(bible_id: UUID, ref_type: str, asset_id: UUID, label: str = "", anchor_strength: float = 0.5, user_id: str = Depends(get_supabase_user)):
    """Add character/background reference to bible."""
    admin = get_supabase_admin()
    current = admin.table('style_bibles').select('id').eq('id', str(bible_id)).eq('owner_id', user_id).maybe_single().execute()
    if not current.data:
        raise HTTPException(404, 'Bible not found')

    admin.table('style_bible_assets').upsert({
        'bible_id': str(bible_id), 'asset_id': str(asset_id),
        'ref_type': ref_type, 'label': label, 'anchor_strength': anchor_strength,
    }, on_conflict='bible_id,asset_id,ref_type').execute()

    return {"status": "added"}
