"""
Routers cho Deep Analysis: get + reanalyze.
Mounted dưới /api/analysis.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task
import uuid


router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/{assistant_id}")
async def get_analysis(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """Lấy analysis mới nhất của assistant (verify ownership)."""
    admin = get_supabase_admin()
    
    # Verify ownership
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
    job_id = str(uuid.uuid4())
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

    analyze_channel_task.delay(job_id, assistant_id)
    
    return {'job_id': job_id, 'status': 'pending'}