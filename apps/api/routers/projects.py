"""
FastAPI router for projects — CRUD + approval + backward compat /start endpoint.
Phase 01: Project foundation & blank onboarding.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.projects import (
    CreateProjectRequest,
    ProjectResponse,
    ProjectListResponse,
    BriefResponse,
    BriefPayload,
    ApprovalRequest,
    ApprovalResponse,
    StageEventResponse,
)
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ============================================================
# Helper: canonical JSON hash for idempotent brief lookup
# ============================================================

def _canonical_json(obj: dict) -> str:
    """Sort keys recursively and return minified JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _brief_hash(brief: BriefPayload) -> str:
    """Compute SHA-256 of canonical brief JSON."""
    payload = brief.model_dump(exclude={"extra"})
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ============================================================
# Legacy: POST /api/projects/start (production — DO NOT REMOVE)
# ============================================================

class StartProjectRequest(BaseModel):
    youtube_url: str

class StartProjectResponse(BaseModel):
    job_id: str
    message: str

@router.post('/start', response_model=StartProjectResponse)
async def start_project(req: StartProjectRequest, user_id: str = Depends(get_supabase_user)):
    """Legacy endpoint: create channel_assistant from YouTube URL."""
    match = re.search(r'@([\w-]+)', req.youtube_url)
    channel_id = match.group(1) if match else req.youtube_url.split('/')[-1]
    cm = CreditManager()
    total_cost = 60
    admin = get_supabase_admin()
    assistant_res = admin.table('channel_assistants').insert({
        'user_id': user_id, 'youtube_url': req.youtube_url,
        'channel_id': channel_id, 'status': 'training'
    }).execute()
    if not assistant_res.data:
        raise HTTPException(500, 'Failed to create assistant')
    assistant_id = assistant_res.data[0]['id']
    job_res = admin.table('jobs').insert({
        'user_id': user_id, 'task_type': 'deep_analysis',
        'input_payload': {'assistant_id': assistant_id, 'channel_id': channel_id, 'youtube_url': req.youtube_url},
        'status': 'pending'
    }).execute()
    job = job_res.data[0]
    job_id = job['id']
    try:
        cm.hold(user_id=user_id, job_id=job_id, amount=total_cost)
    except ValueError as e:
        admin.table('jobs').update({'status': 'failed', 'error_log': str(e)}).eq('id', job_id).execute()
        raise HTTPException(402, str(e))
    task = analyze_channel_task.delay(job_id=job_id, channel_id=channel_id)
    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()
    return StartProjectResponse(job_id=job_id, message='Project started successfully')

# ============================================================
# CRUD: POST /api/projects — Create project (idempotent)
# ============================================================

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(req: CreateProjectRequest, user_id: str = Depends(get_supabase_user)):
    """Create a new project (blank or clone_channel). Idempotent by brief_hash."""
    admin = get_supabase_admin()
    bh = _brief_hash(req.brief)

    existing = admin.table('projects').select('*').eq('user_id', user_id).eq('brief_hash', bh).maybe_single().execute()
    if existing.data:
        return await _build_project_response(admin, existing.data['id'], user_id)

    project_res = admin.table('projects').insert({
        'user_id': user_id,
        'channel_assistant_id': str(req.channel_assistant_id) if req.channel_assistant_id else None,
        'mode': req.mode,
        'status': 'draft',
        'approval_state': 'draft',
        'brief_hash': bh,
        'schema_version': 1,
    }).execute()

    if not project_res.data:
        raise HTTPException(500, 'Failed to create project')

    project = project_res.data[0]
    project_id = project['id']

    brief_res = admin.table('project_briefs').insert({
        'project_id': project_id, 'version': 1,
        'topic': req.brief.topic, 'audience': req.brief.audience,
        'language': req.brief.language,
        'duration_target_seconds': req.brief.duration_target_seconds,
        'aspect_ratio': req.brief.aspect_ratio, 'tone': req.brief.tone,
        'visual_style': req.brief.visual_style,
        'voice_profile_id': str(req.brief.voice_profile_id) if req.brief.voice_profile_id else None,
        'music_mood': req.brief.music_mood,
        'extra': req.brief.extra, 'schema_version': 1,
    }).execute()

    if not brief_res.data:
        raise HTTPException(500, 'Failed to create project brief')

    admin.table('project_stage_events').insert({
        'project_id': project_id, 'stage': 'draft',
        'event_type': 'created',
        'payload': {'mode': req.mode, 'brief_hash': bh},
    }).execute()

    return await _build_project_response(admin, project_id, user_id)

# ============================================================
# CRUD: GET /api/projects — List user's projects (cursor)
# ============================================================

@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user_id: str = Depends(get_supabase_user),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List projects for current user with cursor pagination."""
    admin = get_supabase_admin()
    query = admin.table('projects').select('*', count='exact').eq('user_id', user_id).order('created_at', desc=True).limit(limit)
    if cursor:
        query = query.lt('created_at', cursor)
    res = query.execute()
    projects = []
    for row in (res.data or []):
        projects.append(await _build_project_response(admin, row['id'], user_id))
    next_cursor = projects[-1].created_at.isoformat() if len(projects) == limit else None
    return ProjectListResponse(data=projects, next_cursor=next_cursor, total=res.count or len(projects))


# ============================================================
# CRUD: GET /api/projects/{id} — Get single project
# ============================================================

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get project by ID. Returns 404 for non-owner (no existence leak)."""
    admin = get_supabase_admin()
    return await _build_project_response(admin, str(project_id), user_id)


# ============================================================
# CRUD: POST /api/projects/{id}/approve — Approve or reject
# ============================================================

@router.post("/{project_id}/approve", response_model=ApprovalResponse)
async def approve_project(project_id: UUID, req: ApprovalRequest, user_id: str = Depends(get_supabase_user)):
    """Approve or reject a project."""
    admin = get_supabase_admin()
    project = admin.table('projects').select('*').eq('id', str(project_id)).eq('user_id', user_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(404, 'Project not found')

    update_data = {'approval_state': req.decision}
    if req.decision == 'approved':
        update_data['approved_at'] = datetime.now(timezone.utc).isoformat()
        update_data['status'] = 'approved'

    admin.table('projects').update(update_data).eq('id', str(project_id)).execute()
    admin.table('project_stage_events').insert({
        'project_id': str(project_id), 'stage': req.decision,
        'event_type': req.decision,
        'payload': {'comment': req.comment} if req.comment else {},
    }).execute()
    updated = admin.table('projects').select('*').eq('id', str(project_id)).single().execute()
    return ApprovalResponse(
        project_id=project_id, approval_state=req.decision,
        decision=req.decision, comment=req.comment,
        updated_at=updated.data['updated_at'],
    )


# ============================================================
# CRUD: GET /api/projects/{id}/events — Stage events
# ============================================================

@router.get("/{project_id}/events", response_model=list[StageEventResponse])
async def get_project_events(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get stage events for a project. Verifies ownership first."""
    admin = get_supabase_admin()
    project = admin.table('projects').select('id').eq('id', str(project_id)).eq('user_id', user_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(404, 'Project not found')
    events = admin.table('project_stage_events').select('*').eq('project_id', str(project_id)).order('created_at', desc=True).execute()
    return [StageEventResponse(**e) for e in (events.data or [])]


# ============================================================
# Helper: build ProjectResponse with brief
# ============================================================

async def _build_project_response(admin, project_id: str, user_id: str) -> ProjectResponse:
    project = admin.table('projects').select('*').eq('id', project_id).eq('user_id', user_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(404, 'Project not found')
    p = project.data
    brief_data = None
    brief_rows = admin.table('project_briefs').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    if brief_rows.data:
        b = brief_rows.data[0]
        brief_data = BriefResponse(
            id=b['id'], project_id=b['project_id'], version=b['version'],
            topic=b['topic'], audience=b['audience'], language=b['language'],
            duration_target_seconds=b['duration_target_seconds'],
            aspect_ratio=b['aspect_ratio'], tone=b['tone'],
            visual_style=b['visual_style'],
            voice_profile_id=b.get('voice_profile_id'),
            music_mood=b.get('music_mood'),
            extra=b.get('extra', {}),
            schema_version=b.get('schema_version', 1),
            created_at=b['created_at'],
        )
    return ProjectResponse(
        id=p['id'], user_id=p['user_id'],
        channel_assistant_id=p.get('channel_assistant_id'),
        mode=p['mode'], status=p['status'],
        approval_state=p['approval_state'],
        brief_hash=p['brief_hash'],
        schema_version=p.get('schema_version', 1),
        brief=brief_data,
        created_at=p['created_at'],
        updated_at=p['updated_at'],
        approved_at=p.get('approved_at'),
    )

