"""
Routers cho Deep Analysis: get + reanalyze.
FIXED: No Celery imports - using FastAPI BackgroundTasks
Mounted dưới /api/analysis.
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager


router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _analyze_channel_async(job_id: str, assistant_id: str):
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
        
        db.table('jobs').update({
            'status': 'completed',
            'progress': 100,
        }).eq('id', job_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[analysis] Analysis failed for job {job_id}: {e}")
        
        db.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()


# =============================================================================
# Routes
# =============================================================================

@router.get("/{assistant_id}")
async def get_analysis(assistant_id: str, user_id: str = Depends(get_supabase_user)):
    """Lấy analysis mới nhất của assistant (verify ownership)."""
    admin = get_supabase_admin()
    
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    result = (
        admin.table('channel_deep_analysis')
        .select('*')
        .eq('assistant_id', assistant_id)
        .order('created_at', desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else {}


@router.post("/{assistant_id}/reanalyze")
async def reanalyze(
    assistant_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Trigger lại analysis task (charge 50 credits)."""
    admin = get_supabase_admin()
    
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    manager = CreditManager()
    job_id = str(UUID)
    try:
        manager.hold(user_id, job_id, 50)
    except ValueError as e:
        raise HTTPException(402, f'Insufficient credits: {e}')

    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'task_type': 'deep_analysis',
        'status': 'pending',
        'credits_held': 50,
        'assistant_id': assistant_id,
    }).execute()

    # Queue via BackgroundTasks
    background_tasks.add_task(_analyze_channel_async, job_id, assistant_id)
    
    return {'job_id': job_id, 'status': 'pending'}
