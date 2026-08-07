"""
Scripts Router — Async Scene Breakdown
Tier 1 P0 — Replacing Celery with FastAPI BackgroundTasks

Routes:
- POST /api/scripts/{id}/breakdown — Break script into scenes
- GET /api/scripts/{id}/scenes — Get scene breakdown
- POST /api/scripts/{id}/scenes/regenerate — Regenerate scenes
"""
from __future__ import annotations
from uuid import UUID
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/scripts", tags=["Scripts"])


# =============================================================================
# Constants
# =============================================================================

SCENE_CONTRACT_VERSION: Literal[1] = 1


# =============================================================================
# Schemas
# =============================================================================

class SceneContract(BaseModel):
    """Scene contract v1."""
    schema_version: int = SCENE_CONTRACT_VERSION
    scene_id: str
    scene_index: int
    narration: str
    visual_description: str
    image_prompt: str
    video_prompt: str
    asset_type: str = "Image"
    estimated_duration: float
    characters: list = []
    background: str = ""
    continuity_references: list = []
    status: str = "draft"


class BreakdownRequest(BaseModel):
    """Request to break script into scenes."""
    target_duration_minutes: Optional[int] = 10


class BreakdownResponse(BaseModel):
    """Response after triggering scene breakdown."""
    job_id: str
    status: str
    message: str


class SceneListResponse(BaseModel):
    """List of scenes from breakdown."""
    scenes: list[SceneContract]
    total_duration_seconds: float
    scene_count: int


# =============================================================================
# Scene Contract Builder
# =============================================================================

def wrap_scene_contract(scene: dict, scene_index: int, scene_id: str) -> SceneContract:
    """Wrap raw scene dict into versioned scene contract (v1)."""
    return SceneContract(
        schema_version=SCENE_CONTRACT_VERSION,
        scene_id=scene_id,
        scene_index=scene_index,
        narration=scene.get("narration", scene.get("text", "")),
        visual_description=scene.get("visual_description", ""),
        image_prompt=scene.get("image_prompt", ""),
        video_prompt=scene.get("video_prompt", ""),
        asset_type=scene.get("asset_type", "Image"),
        estimated_duration=scene.get("estimated_duration", scene.get("duration_seconds", 0.0)),
        characters=scene.get("characters", []),
        background=scene.get("background", ""),
        continuity_references=scene.get("continuity_references", []),
        status="draft",
    )


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _breakdown_scenes_async(job_id: str, script_id: str, assistant_id: str, target_duration_minutes: int):
    """
    Async task to break script into scenes.
    Called by BackgroundTasks - no return value needed.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    from openai import OpenAI
    import uuid
    
    db = get_supabase_admin()
    
    try:
        # Get script
        script = db.table('generated_scripts').select('*').eq('id', script_id).maybe_single().execute()
        if not script.data:
            return
        
        # Get assistant pacing
        pacing_wpm = 150
        if assistant_id:
            assistant = db.table('channel_assistants').select('pacing_profile').eq('id', assistant_id).maybe_single().execute()
            if assistant.data:
                pacing_wpm = assistant.data.get('pacing_profile', {}).get('wpm', 150)
        
        # Import SceneBreaker service
        from apps.worker.services.scene_breaker import SceneBreaker
        
        breaker = SceneBreaker(default_wpm=pacing_wpm)
        
        # Get script text
        script_data = script.data
        script_text = script_data.get('body', script_data.get('script_text', ''))
        
        # Segment scenes
        scenes = breaker.segment_scenes(
            script_text=script_text,
            pacing_wpm=pacing_wpm,
            target_duration_minutes=target_duration_minutes,
        )
        
        # Translate B-roll keywords
        all_keywords = []
        for scene in scenes:
            all_keywords.extend(scene.get('broll_keywords', []))
        
        if all_keywords:
            try:
                openai = OpenAI()
                translations = await breaker.translate_broll_keywords(all_keywords, openai)
                translation_map = {t.get('vn'): t for t in translations if isinstance(t, dict) and 'vn' in t}
                
                for scene in scenes:
                    scene['broll_translations'] = [
                        translation_map[kw]
                        for kw in scene.get('broll_keywords', [])
                        if kw in translation_map
                    ]
            except Exception:
                for scene in scenes:
                    scene['broll_translations'] = []
        else:
            for scene in scenes:
                scene['broll_translations'] = []
        
        # Calculate stats
        stats = breaker.calculate_total_duration(scenes)
        
        # Wrap scenes in contract
        wrapped_scenes = [
            wrap_scene_contract(scene, i, f"scene_{uuid.uuid4().hex[:8]}")
            for i, scene in enumerate(scenes)
        ]
        
        # Save to DB
        db.table('generated_scripts').update({
            'scenes': [s.model_dump() for s in wrapped_scenes],
            'scene_count': len(wrapped_scenes),
            'total_duration_seconds': stats['total_duration_seconds'],
        }).eq('id', script_id).execute()
        
        # Update job
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
            'result_payload': {
                'scenes': [s.model_dump() for s in wrapped_scenes],
                **stats,
            },
        }).eq('id', job_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[scenes] Breakdown failed for script {script_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()


# =============================================================================
# Routes
# =============================================================================

@router.get("/{script_id}/scenes", response_model=SceneListResponse)
async def get_scene_breakdown(
    script_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get scene breakdown for a script.
    GET /api/scripts/{script_id}/scenes
    """
    db = get_supabase_admin()
    
    # Get script with ownership verification
    script = db.table('generated_scripts').select('*, project:projects!inner(user_id)').eq('id', str(script_id)).maybe_single().execute()
    
    if not script.data:
        raise HTTPException(404, "Script not found")
    
    # Verify ownership
    project = script.data.get('project')
    if project and project.get('user_id') != user_id:
        raise HTTPException(403, "Access denied")
    
    scenes = script.data.get('scenes', [])
    
    # Parse into SceneContract
    wrapped_scenes = []
    for i, scene in enumerate(scenes):
        if isinstance(scene, dict):
            wrapped = wrap_scene_contract(
                scene,
                i,
                scene.get('scene_id', f"scene_{i}")
            )
            wrapped_scenes.append(wrapped)
    
    return SceneListResponse(
        scenes=wrapped_scenes,
        total_duration_seconds=script.data.get('total_duration_seconds', 0.0),
        scene_count=len(wrapped_scenes),
    )


@router.post("/{script_id}/breakdown", response_model=BreakdownResponse, status_code=202)
async def trigger_scene_breakdown(
    script_id: UUID,
    req: BreakdownRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """
    Break script into scenes using AI.
    POST /api/scripts/{script_id}/breakdown
    
    Uses FastAPI BackgroundTasks (no Celery/Redis needed).
    """
    db = get_supabase_admin()
    
    # Get script with ownership verification
    script = db.table('generated_scripts').select('*, project:projects!inner(user_id)').eq('id', str(script_id)).maybe_single().execute()
    
    if not script.data:
        raise HTTPException(404, "Script not found")
    
    # Verify ownership
    project = script.data.get('project')
    if project and project.get('user_id') != user_id:
        raise HTTPException(403, "Access denied")
    
    # Check script has content
    script_text = script.data.get('body', script.data.get('script_text', ''))
    if not script_text or len(script_text) < 50:
        raise HTTPException(400, "Script too short for breakdown")
    
    # Get assistant_id
    assistant_id = script.data.get('assistant_id', '')
    
    # Create job
    import uuid
    job_id = str(uuid.uuid4())
    
    db.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'task_type': 'scene_breakdown',
        'status': 'pending',
        'progress': 0,
        'script_id': str(script_id),
    }).execute()
    
    # Queue async task
    background_tasks.add_task(
        _breakdown_scenes_async,
        job_id,
        str(script_id),
        assistant_id,
        req.target_duration_minutes or 10,
    )
    
    return BreakdownResponse(
        job_id=job_id,
        status="processing",
        message="Scene breakdown started. Check status at GET /api/jobs/{job_id}",
    )


@router.post("/{script_id}/scenes/regenerate", response_model=BreakdownResponse, status_code=202)
async def regenerate_scenes(
    script_id: UUID,
    req: BreakdownRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """
    Regenerate scene breakdown with new parameters.
    POST /api/scripts/{script_id}/scenes/regenerate
    """
    # Same as breakdown but allows re-generation
    return await trigger_scene_breakdown(script_id, req, background_tasks, user_id)


@router.get("/{script_id}/breakdown/status")
async def get_breakdown_status(
    script_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get breakdown job status.
    GET /api/scripts/{script_id}/breakdown/status
    """
    db = get_supabase_admin()
    
    job = db.table('jobs').select('id, status, progress, error_message').eq('script_id', str(script_id)).eq('task_type', 'scene_breakdown').order('created_at', desc=True).limit(1).maybe_single().execute()
    
    if job.data:
        return job.data
    
    return {
        "status": "not_started",
        "progress": 0,
    }
