"""
Routers cho Jobs: trigger, get, recent.
FIXED: No Celery imports - using FastAPI BackgroundTasks
Mounted dưới /api/jobs.
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
import uuid


router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


VALID_TASK_TYPES = {
    'deep_analysis': 50,
    'idea_generation': 5,
    'script_generation': 30,
    'scene_breakdown': 10,
}


# =============================================================================
# Async Tasks (Background)
# =============================================================================

async def _analyze_channel_async(job_id: str, assistant_id: str, user_id: str):
    """
    Async task to analyze channel.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        db.table('jobs').update({
            'status': 'running',
            'progress': 10,
        }).eq('id', job_id).execute()
        
        # Placeholder: implement actual channel analysis
        # For now, just mark as completed
        
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('id', job_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[jobs] Analysis failed for job {job_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()


async def _generate_ideas_async(job_id: str, assistant_id: str, user_id: str):
    """
    Async task to generate ideas.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        db.table('jobs').update({
            'status': 'running',
            'progress': 10,
        }).eq('id', job_id).execute()
        
        # Placeholder: implement actual idea generation
        
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('id', job_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[jobs] Idea generation failed for job {job_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()


async def _generate_script_async(job_id: str, assistant_id: str, user_id: str, topic: str = None):
    """
    Async task to generate script.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        db.table('jobs').update({
            'status': 'running',
            'progress': 10,
        }).eq('id', job_id).execute()
        
        # Placeholder: implement actual script generation
        
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('id', job_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[jobs] Script generation failed for job {job_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()


# =============================================================================
# Routes
# =============================================================================

class TriggerJobRequest(BaseModel):
    assistant_id: str = Field(..., description="UUID")
    task_type: str = Field(..., description="deep_analysis | idea_generation | script_generation | scene_breakdown")


@router.post("/trigger")
async def trigger_job(
    request: TriggerJobRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Trigger 1 task cho assistant."""
    if request.task_type not in VALID_TASK_TYPES:
        raise HTTPException(400, f"task_type phải là một trong: {list(VALID_TASK_TYPES.keys())}")

    admin = get_supabase_admin()

    # Verify ownership
    assistant = (
        admin.table('channel_assistants')
        .select('id, channel_id, status')
        .eq('id', request.assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    # Hold credits
    manager = CreditManager()
    job_id = str(uuid.uuid4())
    try:
        manager.hold(user_id, job_id, VALID_TASK_TYPES[request.task_type])
    except ValueError as e:
        raise HTTPException(402, f'Insufficient credits: {e}')

    # Insert jobs row
    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'task_type': request.task_type,
        'status': 'pending',
        'credits_held': VALID_TASK_TYPES[request.task_type],
        'assistant_id': request.assistant_id,
        'channel_id': assistant.data.get('channel_id'),
    }).execute()

    # Dispatch via BackgroundTasks
    if request.task_type == 'deep_analysis':
        background_tasks.add_task(_analyze_channel_async, job_id, request.assistant_id, user_id)
    elif request.task_type == 'idea_generation':
        background_tasks.add_task(_generate_ideas_async, job_id, request.assistant_id, user_id)
    elif request.task_type == 'script_generation':
        background_tasks.add_task(_generate_script_async, job_id, request.assistant_id, user_id, None)
    elif request.task_type == 'scene_breakdown':
        # scene_breakdown is handled by /api/scripts/{id}/breakdown
        admin.table('jobs').update({'status': 'completed'}).eq('id', job_id).execute()

    return {
        'job_id': job_id,
        'task_type': request.task_type,
        'status': 'pending',
    }


@router.get("/{job_id}")
async def get_job(job_id: str, user_id: str = Depends(get_supabase_user)):
    """Lấychi tiết job. Verify ownership."""
    admin = get_supabase_admin()
    result = (
        admin.table('jobs')
        .select('*')
        .eq('id', job_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, 'Job not found')
    return result.data


@router.get("/recent/list")
async def get_recent_jobs(user_id: str = Depends(get_supabase_user), limit: int = 10):
    """Lấy N jobs gần nhất của user (cho dashboard)."""
    admin = get_supabase_admin()
    result = (
        admin.table('jobs')
        .select('id, task_type, status, credits_held, created_at, assistant_id')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .limit(min(limit, 50))
        .execute()
    )
    return result.data or []
