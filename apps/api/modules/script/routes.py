"""
API router for script generation endpoints.
CLEANED: Removed Celery imports - scene_breakdown now uses FastAPI BackgroundTasks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
import json

router = APIRouter(prefix="/api/scripts", tags=["Script Generation"])


class GenerateScriptRequest(BaseModel):
    assistant_id: UUID
    topic: str


class ScriptResponse(BaseModel):
    id: str
    topic: str
    script: dict
    score: float = 0
    cost_usd: float = 0
    scenes: list = []
    created_at: str


@router.get('/{script_id}', response_model=ScriptResponse)
async def get_script(
    script_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get generated script by ID.
    GET /api/scripts/{script_id}
    """
    db = get_supabase_admin()

    # Get script
    script = (
        db.table('generated_scripts')
        .select('*')
        .eq('id', str(script_id))
        .maybe_single()
        .execute()
    )

    if not script.data:
        raise HTTPException(404, 'Script not found')

    # Verify ownership via assistant
    assistant = (
        db.table('channel_assistants')
        .select('user_id')
        .eq('id', script.data.get('assistant_id'))
        .maybe_single()
        .execute()
    )

    if not assistant.data or assistant.data.get('user_id') != user_id:
        raise HTTPException(403, 'Forbidden')

    # Parse script JSON
    try:
        script_data = json.loads(script.data['script_text'])
    except Exception:
        script_data = script.data['script_text']

    return ScriptResponse(
        id=script.data['id'],
        topic=script.data.get('topic', ''),
        script=script_data,
        score=script.data.get('score', 0),
        cost_usd=script.data.get('cost_usd', 0),
        scenes=script.data.get('scenes', []),
        created_at=script.data.get('created_at', ''),
    )


# NOTE: 
# - POST /api/scripts/{id}/breakdown — handled by apps/api/routers/scripts.py
# - GET /api/scripts/{id}/scenes — handled by apps/api/routers/scripts.py
