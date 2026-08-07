"""
Subtitles Router — Async SRT Generation
Tier 1 P0 — Replacing Celery with FastAPI BackgroundTasks

Routes:
- POST /api/projects/{id}/subtitles/generate — Generate SRT from voice_lines
- GET /api/projects/{id}/subtitles — List subtitle tracks
- GET /api/subtitles/{track_id}/download — Download SRT file
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/projects", tags=["Subtitles"])


# =============================================================================
# Schemas
# =============================================================================

class SubtitleTrackResponse(BaseModel):
    """Subtitle track response."""
    id: str
    project_id: str
    format: str
    storage_key: str
    version: int
    status: str
    created_at: Optional[str] = None


class SubtitleGenerateRequest(BaseModel):
    """Request to generate subtitles."""
    force_regenerate: bool = False


class SubtitleGenerateResponse(BaseModel):
    """Response after triggering subtitle generation."""
    track_id: str
    status: str
    message: str


class SubtitleStatusResponse(BaseModel):
    """Status of subtitle generation job."""
    track_id: Optional[str] = None
    status: str
    progress: int
    message: Optional[str] = None


# =============================================================================
# SRT Helpers
# =============================================================================

def sec_to_srt(seconds: float) -> str:
    """Convert float seconds to SRT timestamp: HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt_content(voice_lines: list[dict]) -> str:
    """Build SRT content from ordered voice_lines."""
    blocks = []
    cursor = 0.0
    for line in voice_lines:
        dur = float(line.get('duration_seconds') or 0)
        if dur <= 0:
            dur = 3.0  # fallback
        start = cursor
        end = start + dur
        idx = len(blocks) + 1
        blocks.append(f"{idx}\n{sec_to_srt(start)} --> {sec_to_srt(end)}\n{line.get('text', '')}\n")
        cursor = end
    return "\n".join(blocks)


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _generate_srt_async(project_id: str, user_id: str):
    """
    Async task to generate SRT file.
    Called by BackgroundTasks - no return value needed.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    
    db = get_supabase_admin()
    
    try:
        # Get all voice_lines for project via scenes
        scenes = db.table('project_scenes').select('id').eq('project_id', project_id).execute()
        if not scenes.data:
            return
        
        scene_ids = [s['id'] for s in scenes.data]
        lines_res = db.table('voice_lines').select('*').in_('scene_id', scene_ids).order('created_at').execute()
        
        voice_lines = lines_res.data or []
        if not voice_lines:
            return
        
        # Build SRT
        srt_content = build_srt_content(voice_lines)
        storage_key = f"srt/{project_id}/subtitle_v1.srt"
        
        # Get next version
        latest = db.table('subtitle_tracks').select('version').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
        next_ver = (latest.data[0]['version'] + 1) if latest.data else 1
        
        # Save to R2
        try:
            from apps.api.services.storage import get_storage_service
            storage = get_storage_service()
            public_url = storage.upload_text(
                content=srt_content,
                key=storage_key,
                content_type='text/plain',
            )
        except Exception:
            public_url = f"https://cdn.ai86.click/{storage_key}"
        
        # Insert track record
        db.table('subtitle_tracks').insert({
            'project_id': project_id,
            'format': 'srt',
            'storage_key': storage_key,
            'version': next_ver,
            'status': 'generated',
        }).execute()
        
        # Update job if exists
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('project_id', project_id).eq('task_type', 'subtitle_generate').execute()
        
    except Exception as e:
        # Log error but don't fail silently
        import logging
        logging.error(f"[subtitles] SRT generation failed for {project_id}: {e}")
        
        # Update job status if exists
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('project_id', project_id).eq('task_type', 'subtitle_generate').execute()


# =============================================================================
# Routes
# =============================================================================

@router.get("/{project_id}/subtitles", response_model=list[SubtitleTrackResponse])
async def list_subtitle_tracks(
    project_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    List all subtitle tracks for a project.
    GET /api/projects/{project_id}/subtitles
    """
    db = get_supabase_admin()
    
    # Verify project ownership
    project = db.table('projects').select('id').eq('id', str(project_id)).eq('user_id', user_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(404, "Project not found")
    
    result = db.table('subtitle_tracks').select('*').eq('project_id', str(project_id)).order('version', desc=True).execute()
    
    tracks = []
    for row in (result.data or []):
        tracks.append(SubtitleTrackResponse(
            id=row.get('id', ''),
            project_id=row.get('project_id', ''),
            format=row.get('format', 'srt'),
            storage_key=row.get('storage_key', ''),
            version=row.get('version', 1),
            status=row.get('status', 'generated'),
            created_at=row.get('created_at'),
        ))
    
    return tracks


@router.post("/{project_id}/subtitles/generate", response_model=SubtitleGenerateResponse, status_code=202)
async def generate_subtitles(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """
    Generate SRT subtitles from voice_lines.
    POST /api/projects/{project_id}/subtitles/generate
    
    Uses FastAPI BackgroundTasks (no Celery/Redis needed).
    """
    db = get_supabase_admin()
    
    # Verify project ownership
    project = db.table('projects').select('id').eq('id', str(project_id)).eq('user_id', user_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(404, "Project not found")
    
    # Check if voice_lines exist
    scenes = db.table('project_scenes').select('id').eq('project_id', str(project_id)).execute()
    if not scenes.data:
        raise HTTPException(400, "No scenes found. Generate script and voice first.")
    
    scene_ids = [s['id'] for s in scenes.data]
    lines_res = db.table('voice_lines').select('id').in_('scene_id', scene_ids).limit(1).execute()
    if not lines_res.data:
        raise HTTPException(400, "No voice lines found. Generate voice synthesis first.")
    
    # Get next version for track_id
    latest = db.table('subtitle_tracks').select('id, version').eq('project_id', str(project_id)).order('version', desc=True).limit(1).execute()
    next_ver = (latest.data[0]['version'] + 1) if latest.data else 1
    track_id = latest.data[0]['id'] if latest.data else str(project_id)
    
    # Queue async task
    background_tasks.add_task(_generate_srt_async, str(project_id), user_id)
    
    return SubtitleGenerateResponse(
        track_id=track_id,
        status="processing",
        message=f"Subtitle generation started (v{next_ver}). Check status at GET /api/projects/{project_id}/subtitles",
    )


@router.get("/{project_id}/subtitles/status", response_model=SubtitleStatusResponse)
async def get_subtitle_status(
    project_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get current subtitle generation status.
    GET /api/projects/{project_id}/subtitles/status
    """
    db = get_supabase_admin()
    
    # Check latest track
    track = db.table('subtitle_tracks').select('id, status').eq('project_id', str(project_id)).order('version', desc=True).limit(1).maybe_single().execute()
    
    if track.data:
        return SubtitleStatusResponse(
            track_id=track.data.get('id'),
            status=track.data.get('status', 'unknown'),
            progress=100 if track.data.get('status') == 'generated' else 50,
            message=None,
        )
    
    # Check if job is running
    job = db.table('jobs').select('status, progress').eq('project_id', str(project_id)).eq('task_type', 'subtitle_generate').order('created_at', desc=True).limit(1).maybe_single().execute()
    
    if job.data:
        return SubtitleStatusResponse(
            track_id=None,
            status=job.data.get('status', 'unknown'),
            progress=job.data.get('progress', 0),
            message=None,
        )
    
    return SubtitleStatusResponse(
        track_id=None,
        status="not_started",
        progress=0,
        message="No subtitles generated yet",
    )


@router.get("/subtitles/{track_id}/download")
async def download_subtitle(
    track_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Download SRT file content.
    GET /api/projects/subtitles/{track_id}/download
    """
    db = get_supabase_admin()
    
    track = db.table('subtitle_tracks').select('*, project:projects!inner(user_id)').eq('id', str(track_id)).maybe_single().execute()
    
    if not track.data:
        raise HTTPException(404, "Subtitle track not found")
    
    # Verify ownership via project
    project = track.data.get('project')
    if project and project.get('user_id') != user_id:
        raise HTTPException(403, "Access denied")
    
    storage_key = track.data.get('storage_key', '')
    if not storage_key:
        raise HTTPException(400, "No storage key found")
    
    # Fetch from R2
    try:
        from apps.api.services.storage import get_storage_service
        storage = get_storage_service()
        content = storage.download_text(storage_key)
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=subtitle_v{track.data.get('version', 1)}.srt"},
        )
    except Exception:
        # Fallback: return empty content
        from fastapi.responses import Response
        return Response(content="", media_type="text/plain")
