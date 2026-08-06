"""
FastAPI router for thumbnail + metadata — Phase 05.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.thumbnail import (
    ThumbnailGenerateRequest, ThumbnailCandidateResponse,
    ThumbnailSelectRequest, MetadataBuildResponse,
    CleanupPreviewResponse, CleanupApproveRequest,
)

router = APIRouter(prefix="/api/projects", tags=["Thumbnail"])


def _verify_owner(admin, project_id: str, user_id: str):
    p = admin.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).maybe_single().execute()
    if not p.data:
        raise HTTPException(404, 'Project not found')


@router.post("/{project_id}/thumbnail/generate")
async def generate_thumbnails(project_id: UUID, req: ThumbnailGenerateRequest, user_id: str = Depends(get_supabase_user)):
    """Generate AI thumbnail candidates."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    try:
        from apps.worker.tasks.thumbnail_generate import thumbnail_generate
        task = thumbnail_generate.delay(pid, provider=req.provider, count=req.count)
        return {"status": "enqueued", "task_id": task.id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{project_id}/thumbnail/candidates", response_model=list[ThumbnailCandidateResponse])
async def get_thumbnail_candidates(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get thumbnail candidates for project."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    candidates = admin.table('thumbnail_candidates').select('*').eq('project_id', pid).order('score', desc=True).execute()
    return [ThumbnailCandidateResponse(**c) for c in (candidates.data or [])]


@router.post("/{project_id}/thumbnail/select")
async def select_thumbnail(project_id: UUID, req: ThumbnailSelectRequest, user_id: str = Depends(get_supabase_user)):
    """Select a thumbnail candidate."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    admin.table('thumbnail_candidates').update({'selected': False}).eq('project_id', pid).neq('id', str(req.candidate_id)).execute()
    admin.table('thumbnail_candidates').update({'selected': True}).eq('id', str(req.candidate_id)).execute()
    return {"status": "selected", "candidate_id": str(req.candidate_id)}


@router.post("/{project_id}/metadata/build", response_model=MetadataBuildResponse)
async def build_metadata(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Build metadata package."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    try:
        from apps.worker.tasks.metadata_package import metadata_package
        result = metadata_package.delay(pid)
        exports = admin.table('project_exports').select('*').eq('project_id', pid).order('version', desc=True).limit(1).single().execute()
        if exports.data:
            return MetadataBuildResponse(**exports.data)
        raise HTTPException(500, 'Build failed')
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{project_id}/metadata", response_model=MetadataBuildResponse)
async def get_metadata(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get latest metadata package."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    exp = admin.table('project_exports').select('*').eq('project_id', pid).order('version', desc=True).limit(1).maybe_single().execute()
    if not exp.data:
        raise HTTPException(404, 'No metadata built yet')
    return MetadataBuildResponse(**exp.data)
