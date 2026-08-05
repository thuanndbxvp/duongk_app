"""
API router for script generation endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.worker.tasks.script_generate import run as script_generate_task
from supabase import create_client
import os

router = APIRouter(prefix="/api/scripts", tags=["Script Generation"])

class GenerateScriptRequest(BaseModel):
    assistant_id: UUID
    topic: str
    user_id: UUID  # Pass user_id directly since we don't have auth dependency

class ScriptResponse(BaseModel):
    job_id: str
    status: str
    message: str

@router.post('/generate', response_model=ScriptResponse)
async def generate_script(req: GenerateScriptRequest):
    admin = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Verify assistant belongs to user
    assistant = admin.table('channel_assistants').select('id').eq('id', str(req.assistant_id)).eq('user_id', str(req.user_id)).single().execute()
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found or does not belong to user')

    # Create job
    job_result = admin.table('jobs').insert({
        'user_id': str(req.user_id),
        'task_type': 'script_generate',
        'input_payload': {
            'assistant_id': str(req.assistant_id),
            'topic': req.topic,
        },
        'status': 'pending',
    }).execute()

    if not job_result.data:
        raise HTTPException(500, 'Failed to create job')

    job = job_result.data[0]
    job_id = job['id']

    # Enqueue task
    task = script_generate_task.delay(
        job_id=job_id,
        assistant_id=str(req.assistant_id),
        topic=req.topic,
    )

    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()

    return ScriptResponse(
        job_id=job_id,
        status='pending',
        message=f'Script generation started. Track at /api/jobs/{job_id}',
    )
