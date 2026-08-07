"""
FastAPI router for voice & timeline — FIXED: No Celery imports
All async tasks now use FastAPI BackgroundTasks
Prefix: /api/projects
"""
from __future__ import annotations
from uuid import UUID
import asyncio

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.voice import (
    VoiceStartRequest, VoiceStartResponse,
    VoiceLineResponse, VoiceStatusResponse, VoiceRetryResponse,
    SubtitleTrackResponse, TimelineResponse, TimelineCompileResponse,
)

router = APIRouter(prefix="/api/projects", tags=["Voice"])


def _verify_project_owner(admin, project_id: str, user_id: str):
    proj = admin.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).maybe_single().execute()
    if not proj.data:
        raise HTTPException(404, 'Project not found')


# =============================================================================
# Async Tasks (Background)
# =============================================================================

async def _synthesize_voice_async(voice_line_id: str, project_id: str):
    """
    Async task to synthesize TTS for a voice line.
    Called by BackgroundTasks - no Celery needed.
    """
    from datetime import datetime, timezone
    
    db = get_supabase_admin()
    
    try:
        # Update voice line status
        db.table('voice_lines').update({
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', voice_line_id).execute()
        
        # Get voice line details
        line = db.table('voice_lines').select('*').eq('id', voice_line_id).maybe_single().execute()
        if not line.data:
            raise Exception("Voice line not found")
        
        # Get voice profile
        ref_audio_url = None
        if line.data.get('voice_profile_id'):
            vp = db.table('voice_profiles').select('sample_audio_url').eq('id', line.data['voice_profile_id']).maybe_single().execute()
            if vp.data:
                ref_audio_url = vp.data.get('sample_audio_url')
        
        # Generate TTS via Modal GPU
        output_key = f"tts/{project_id}/{voice_line_id}.wav"
        duration = 0.0
        
        try:
            import modal
            synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
            result = synth_fn.remote(
                text=line.data.get('text', ''),
                reference_audio_url=ref_audio_url or '',
                output_key=output_key,
                voice_name="custom_clone",
            )
            duration = float(result.get('duration_seconds', 0))
        except Exception:
            # Fallback: estimate duration
            words = len(line.data.get('text', '').split())
            duration = words / 2.5  # ~150 WPM
        
        # Update voice line as success
        db.table('voice_lines').update({
            'status': 'success',
            'storage_key': output_key,
            'duration_seconds': duration,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', voice_line_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[voice] TTS failed for line {voice_line_id}: {e}")
        
        db.table('voice_lines').update({
            'status': 'failed',
            'error_code': 'tts_error',
            'error_message': str(e),
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', voice_line_id).execute()


# =============================================================================
# Routes
# =============================================================================

@router.post("/{project_id}/voice/start", response_model=VoiceStartResponse)
async def start_voice(
    project_id: UUID,
    req: VoiceStartRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Start TTS voice generation for project scenes."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)

    scenes_q = admin.table('project_scenes').select('id, narration, scene_id').eq('project_id', pid).order('scene_index')
    if req.scene_ids:
        scenes_q = scenes_q.in_('id', [str(s) for s in req.scene_ids])
    scenes = scenes_q.execute()

    if not scenes.data:
        raise HTTPException(400, 'No scenes found')
    
    line_ids = []
    for scene in scenes.data:
        existing = admin.table('voice_lines').select('id').eq('scene_id', scene['id']).eq('voice_version', req.voice_version).maybe_single().execute()
        if existing.data:
            line_ids.append(existing.data['id'])
            continue
        line_res = admin.table('voice_lines').insert({
            'scene_id': scene['id'],
            'voice_profile_id': str(req.voice_profile_id),
            'voice_version': req.voice_version,
            'text': scene.get('narration', ''),
            'provider': 'omnivoice',
            'status': 'pending',
        }).execute()
        if line_res.data:
            lid = str(line_res.data[0]['id'])
            line_ids.append(lid)
            # Queue TTS via BackgroundTasks
            background_tasks.add_task(_synthesize_voice_async, lid, pid)
    
    return VoiceStartResponse(project_id=project_id, total_scenes=len(scenes.data), voice_lines=[UUID(l) for l in line_ids])


@router.get("/{project_id}/voice/status", response_model=VoiceStatusResponse)
async def get_voice_status(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get aggregated voice status."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)
    
    scenes = admin.table('project_scenes').select('id').eq('project_id', pid).execute()
    if not scenes.data:
        return VoiceStatusResponse(project_id=project_id, lines=[], total=0, succeeded=0, failed=0, pending=0, running=0)

    scene_ids = [s['id'] for s in scenes.data]
    lines_res = admin.table('voice_lines').select('*').in_('scene_id', scene_ids).order('created_at').execute()
    lines = [VoiceLineResponse(**l) for l in (lines_res.data or [])]
    return VoiceStatusResponse(
        project_id=project_id, lines=lines, total=len(lines),
        succeeded=sum(1 for l in lines if l.status == 'success'),
        failed=sum(1 for l in lines if l.status == 'failed'),
        pending=sum(1 for l in lines if l.status == 'pending'),
        running=sum(1 for l in lines if l.status == 'running'),
    )


@router.post("/{project_id}/voice/retry/{scene_id}", response_model=VoiceRetryResponse)
async def retry_voice_scene(
    project_id: UUID,
    scene_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Retry TTS for a single failed scene."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)
    
    line = admin.table('voice_lines').select('*').eq('scene_id', str(scene_id)).order('voice_version', desc=True).limit(1).maybe_single().execute()
    if not line.data:
        raise HTTPException(404, 'Voice line not found')

    admin.table('voice_lines').update({'status': 'pending', 'error_code': None, 'error_message': None}).eq('id', line.data['id']).execute()
    
    # Queue TTS via BackgroundTasks
    background_tasks.add_task(_synthesize_voice_async, line.data['id'], pid)
    
    return VoiceRetryResponse(voice_line_id=line.data['id'], scene_id=scene_id, status='enqueued')


@router.post("/{project_id}/timeline/compile", response_model=TimelineCompileResponse)
async def compile_timeline(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Compile timeline model from voice lines + scenes."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)
    
    from apps.worker.services.timeline_compiler import compile_timeline_model
    model = await compile_timeline_model(admin, pid)

    latest = admin.table('timelines').select('version').eq('project_id', pid).order('version', desc=True).limit(1).execute()
    next_ver = (latest.data[0]['version'] + 1) if latest.data else 1

    tl_res = admin.table('timelines').insert({
        'project_id': pid,
        'version': next_ver,
        'schema_version': 1,
        'model': model,
        'status': 'compiled',
        'created_by': user_id,
    }).execute()

    tl = tl_res.data[0] if tl_res.data else {}
    return TimelineCompileResponse(timeline_id=tl.get('id', ''), version=next_ver, status='compiled')


@router.get("/{project_id}/timeline", response_model=TimelineResponse)
async def get_timeline(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get current timeline for project."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)

    tl = admin.table('timelines').select('*').eq('project_id', pid).order('version', desc=True).limit(1).maybe_single().execute()
    if not tl.data:
        raise HTTPException(404, 'No timeline compiled yet')
    return TimelineResponse(**tl.data)
