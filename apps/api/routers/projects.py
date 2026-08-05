from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task
import re

router = APIRouter(prefix="/api/projects", tags=["Projects"])

class StartProjectRequest(BaseModel):
    youtube_url: str

class StartProjectResponse(BaseModel):
    job_id: str
    message: str

@router.post('/start', response_model=StartProjectResponse)
async def start_project(req: StartProjectRequest, user_id: str = Depends(get_supabase_user)):
    # 1. Parse Handle
    match = re.search(r'@([\w-]+)', req.youtube_url)
    channel_id = match.group(1) if match else req.youtube_url.split('/')[-1]
    
    # 2. Charge credits (60 for full analysis)
    cm = CreditManager()
    total_cost = 60
    
    admin = get_supabase_admin()
    
    # 3. Create Assistant
    assistant_res = admin.table('channel_assistants').insert({
        'user_id': user_id,
        'youtube_url': req.youtube_url,
        'channel_id': channel_id,
        'status': 'training'
    }).execute()
    
    if not assistant_res.data:
        raise HTTPException(500, 'Failed to create assistant')
    
    assistant_id = assistant_res.data[0]['id']
    
    # 4. Create Job
    job_res = admin.table('jobs').insert({
        'user_id': user_id,
        'task_type': 'deep_analysis',
        'input_payload': {
            'assistant_id': assistant_id,
            'channel_id': channel_id,
            'youtube_url': req.youtube_url
        },
        'status': 'pending'
    }).execute()
    
    job = job_res.data[0]
    job_id = job['id']
    
    # Hold credits
    try:
        cm.hold(user_id=user_id, job_id=job_id, amount=total_cost)
    except ValueError as e:
        # Rollback job if insufficient credits
        admin.table('jobs').update({'status': 'failed', 'error_log': str(e)}).eq('id', job_id).execute()
        raise HTTPException(402, str(e))
    
    # 5. Start Celery Task
    task = analyze_channel_task.delay(job_id=job_id, channel_id=channel_id)
    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()
    
    return StartProjectResponse(
        job_id=job_id,
        message='Project started successfully'
    )
