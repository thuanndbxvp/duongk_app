"""
FastAPI router for voice & timeline — Phase 03.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

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


@router.post("/{project_id}/voice/start", response_model=VoiceStartResponse)
async def start_voice(project_id: UUID, req: VoiceStartRequest, user_id: str = Depends(get_supabase_user)):
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
            'scene_id': scene['id'], 'voice_profile_id': str(req.voice_profile_id),
            'voice_version': req.voice_version, 'text': scene.get('narration', ''),
            'provider': 'omnivoice', 'status': 'pending',
        }).execute()
        if line_res.data:
            lid = str(line_res.data[0]['id'])
            line_ids.append(lid)
            try:
                from apps.worker.tasks.tts_scene import tts_scene
                tts_scene.delay(lid)
            except Exception:
                pass

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
async def retry_voice_scene(project_id: UUID, scene_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Retry TTS for a single failed scene."""
    admin = get_supabase_admin()
    _verify_project_owner(admin, str(project_id), user_id)

    line = admin.table('voice_lines').select('*').eq('scene_id', str(scene_id)).order('voice_version', desc=True).limit(1).maybe_single().execute()
    if not line.data:
        raise HTTPException(404, 'Voice line not found')

    admin.table('voice_lines').update({'status': 'pending', 'error_code': None, 'error_message': None}).eq('id', line.data['id']).execute()
    try:
        from apps.worker.tasks.tts_scene import tts_scene
        tts_scene.delay(line.data['id'])
    except Exception:
        pass
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
        'project_id': pid, 'version': next_ver, 'schema_version': 1,
        'model': model, 'status': 'compiled', 'created_by': user_id,
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

