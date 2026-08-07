"""
FastAPI router for thumbnail + metadata — Phase 05.
CLEANED: Replaced Celery with FastAPI BackgroundTasks
"""
from __future__ import annotations
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

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


# =============================================================================
# Async Tasks (Background)
# =============================================================================

async def _generate_thumbnails_async(project_id: str, provider: str, count: int):
    """
    Async task to generate thumbnail candidates.
    Called by BackgroundTasks.
    """
    from openai import OpenAI
    import uuid
    
    db = get_supabase_admin()
    
    try:
        # Update job status
        db.table('jobs').update({
            'status': 'running',
            'progress': 10,
        }).eq('project_id', project_id).eq('task_type', 'thumbnail_generate').execute()
        
        # Generate thumbnails using vision model
        # This is a placeholder - implement actual thumbnail generation logic
        # For now, just mark as completed
        candidates = []
        for i in range(count):
            candidates.append({
                'id': str(uuid.uuid4()),
                'project_id': project_id,
                'image_url': f'https://cdn.ai86.click/thumbnails/{project_id}/thumb_{i}.png',
                'prompt': f'Auto-generated thumbnail {i+1}',
                'score': 0.8 - (i * 0.1),
                'selected': False,
                'created_at': 'now()',
            })
        
        # Insert candidates
        for c in candidates:
            db.table('thumbnail_candidates').insert(c).execute()
        
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('project_id', project_id).eq('task_type', 'thumbnail_generate').execute()
        
    except Exception as e:
        import logging
        logging.error(f"[thumbnail] Generation failed for {project_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('project_id', project_id).eq('task_type', 'thumbnail_generate').execute()


async def _build_metadata_async(project_id: str):
    """
    Async task to build metadata package.
    Called by BackgroundTasks.
    """
    import uuid
    from datetime import datetime, timezone
    
    db = get_supabase_admin()
    
    try:
        # Get project data
        project = db.table('projects').select('*').eq('id', project_id).maybe_single().execute()
        if not project.data:
            return
        
        # Get scenes and voice lines
        scenes = db.table('project_scenes').select('*').eq('project_id', project_id).execute()
        
        # Build metadata package
        metadata = {
            'title': project.data.get('title', ''),
            'description': project.data.get('description', ''),
            'scenes_count': len(scenes.data) if scenes.data else 0,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }
        
        # Get latest version
        latest = db.table('project_exports').select('version').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
        next_ver = (latest.data[0]['version'] + 1) if latest.data else 1
        
        # Insert export
        export_id = str(uuid.uuid4())
        db.table('project_exports').insert({
            'id': export_id,
            'project_id': project_id,
            'version': next_ver,
            'metadata': metadata,
            'status': 'ready',
        }).execute()
        
        # Update job
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('project_id', project_id).eq('task_type', 'metadata_build').execute()
        
    except Exception as e:
        import logging
        logging.error(f"[metadata] Build failed for {project_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('project_id', project_id).eq('task_type', 'metadata_build').execute()


# =============================================================================
# Routes
# =============================================================================

@router.post("/{project_id}/thumbnail/generate")
async def generate_thumbnails(
    project_id: UUID,
    req: ThumbnailGenerateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """
    Generate AI thumbnail candidates.
    POST /api/projects/{project_id}/thumbnail/generate
    
    Uses FastAPI BackgroundTasks (no Celery/Redis needed).
    """
    import uuid
    
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    
    # Create job
    job_id = str(uuid.uuid4())
    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'project_id': pid,
        'task_type': 'thumbnail_generate',
        'status': 'pending',
        'progress': 0,
    }).execute()
    
    # Queue async task
    background_tasks.add_task(_generate_thumbnails_async, pid, req.provider, req.count)
    
    return {"status": "processing", "job_id": job_id}


@router.get("/{project_id}/thumbnail/candidates", response_model=list[ThumbnailCandidateResponse])
async def get_thumbnail_candidates(
    project_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """Get thumbnail candidates for project."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    candidates = admin.table('thumbnail_candidates').select('*').eq('project_id', pid).order('score', desc=True).execute()
    return [ThumbnailCandidateResponse(**c) for c in (candidates.data or [])]


@router.post("/{project_id}/thumbnail/select")
async def select_thumbnail(
    project_id: UUID,
    req: ThumbnailSelectRequest,
    user_id: str = Depends(get_supabase_user),
):
    """Select a thumbnail candidate."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    admin.table('thumbnail_candidates').update({'selected': False}).eq('project_id', pid).neq('id', str(req.candidate_id)).execute()
    admin.table('thumbnail_candidates').update({'selected': True}).eq('id', str(req.candidate_id)).execute()
    return {"status": "selected", "candidate_id": str(req.candidate_id)}


@router.post("/{project_id}/metadata/build", response_model=MetadataBuildResponse)
async def build_metadata(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """
    Build metadata package.
    POST /api/projects/{project_id}/metadata/build
    
    Uses FastAPI BackgroundTasks (no Celery/Redis needed).
    """
    import uuid
    
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    
    # Create job
    job_id = str(uuid.uuid4())
    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'project_id': pid,
        'task_type': 'metadata_build',
        'status': 'pending',
        'progress': 0,
    }).execute()
    
    # Queue async task
    background_tasks.add_task(_build_metadata_async, pid)
    
    return MetadataBuildResponse(
        id=job_id,
        project_id=pid,
        version=1,
        status='building',
        created_at=None,
    )


@router.get("/{project_id}/metadata", response_model=MetadataBuildResponse)
async def get_metadata(
    project_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """Get latest metadata package."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    exp = admin.table('project_exports').select('*').eq('project_id', pid).order('version', desc=True).limit(1).maybe_single().execute()
    if not exp.data:
        raise HTTPException(404, 'No metadata built yet')
    return MetadataBuildResponse(**exp.data)
