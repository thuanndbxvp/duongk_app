"""
Routers cho Jobs: trigger, get, recent.
Mounted dưới /api/jobs.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task
from apps.worker.tasks.idea_generate import run as idea_generate_task
from apps.worker.tasks.script_generate import run as script_generate_task
import uuid


router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


VALID_TASK_TYPES = {
    'deep_analysis': 50,
    'idea_generation': 5,
    'script_generation': 30,
    'scene_breakdown': 10,
}


class TriggerJobRequest(BaseModel):
    assistant_id: str = Field(..., description="UUID")
    task_type: str = Field(..., description="deep_analysis | idea_generation | script_generation | scene_breakdown")


@router.post("/trigger")
async def trigger_job(
    request: TriggerJobRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger 1 task cho assistant.
    
    Args:
        request: {assistant_id, task_type}.
    
    Returns:
        {job_id, task_type, status: 'pending'}.
    
    Raises:
        HTTPException 400 nếu task_type không hợp lệ.
        HTTPException 402 nếu không đủ credits.
        HTTPException 404 nếu assistant không thuộc user.
    """
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

    # Dispatch Celery task
    if request.task_type == 'deep_analysis':
        analyze_channel_task.delay(job_id, request.assistant_id)
    elif request.task_type == 'idea_generation':
        idea_generate_task.delay(job_id, request.assistant_id)
    elif request.task_type == 'script_generation':
        script_generate_task.delay(job_id, request.assistant_id, topic=None)
    elif request.task_type == 'scene_breakdown':
        # scene_breakdown cần script_id, sẽ implement sau
        pass

    return {
        'job_id': job_id,
        'task_type': request.task_type,
        'status': 'pending',
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """Lấy chi tiết job. Verify ownership."""
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
async def get_recent_jobs(
    user_id: str = Depends(get_supabase_user),
    limit: int = 10,
):
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