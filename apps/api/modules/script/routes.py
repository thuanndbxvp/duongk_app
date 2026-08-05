"""
API router for script generation endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.worker.tasks.script_generate import run as script_generate_task
from apps.worker.tasks.scene_breakdown import run as scene_breakdown_task
from supabase import create_client
import os
import json

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

@router.post('/breakdown-scenes', response_model=ScriptResponse)
async def breakdown_scenes(req: GenerateScriptRequest):
    """
    Trigger scene breakdown for latest generated script.
    """
    admin = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get latest script for this assistant
    existing_script = (
        admin.table('generated_scripts')
        .select('*')
        .eq('assistant_id', str(req.assistant_id))
        .order('created_at', desc=True)
        .limit(1)
        .execute()
    )

    if not existing_script.data:
        raise HTTPException(400, 'No script found. Generate a script first.')

    script_data = existing_script.data[0]
    try:
        script_json = json.loads(script_data['script_text'])
    except Exception:
        script_json = script_data['script_text']

    # Create job
    job_result = admin.table('jobs').insert({
        'user_id': str(req.user_id),
        'task_type': 'scene_breakdown',
        'input_payload': {
            'assistant_id': str(req.assistant_id),
            'script_data': script_json,
        },
        'status': 'pending',
    }).execute()

    if not job_result.data:
        raise HTTPException(500, 'Failed to create job')

    job = job_result.data[0]
    job_id = job['id']

    # Enqueue task
    task = scene_breakdown_task.delay(
        job_id=job_id,
        script_data=script_json,
        assistant_id=str(req.assistant_id),
    )

    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()

    return ScriptResponse(
        job_id=job_id,
        status='pending',
        message=f'Scene breakdown started. Track at /api/jobs/{job_id}',
    )

@router.get('/{script_id}')
async def get_script(script_id: UUID, user_id: str):
    """Get generated script by ID."""
    admin = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get script
    script = (
        admin.table('generated_scripts')
        .select('*')
        .eq('id', str(script_id))
        .single()
        .execute()
    )

    if not script.data:
        raise HTTPException(404, 'Script not found')

    # Verify ownership via assistant
    assistant = (
        admin.table('channel_assistants')
        .select('user_id')
        .eq('id', script.data['assistant_id'])
        .single()
        .execute()
    )

    if not assistant.data or str(assistant.data['user_id']) != user_id:
        raise HTTPException(403, 'Forbidden')

    # Parse script JSON
    try:
        script_data = json.loads(script.data['script_text'])
    except Exception:
        script_data = script.data['script_text']

    return {
        'id': script.data['id'],
        'topic': script.data['topic'],
        'script': script_data,
        'score': script.data.get('score', 0),
        'cost_usd': script.data.get('cost_usd', 0),
        'scenes': script.data.get('scenes'),
        'created_at': script.data['created_at'],
    }
