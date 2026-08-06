"""
FastAPI router for render — Phase 04.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.render import (
    RenderStartRequest, RenderStartResponse,
    RenderJobResponse, ExportResponse,
)

router = APIRouter(prefix="/api", tags=["Render"])


def _verify_project_owner(admin, project_id: str, user_id: str):
    proj = admin.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).maybe_single().execute()
    if not proj.data:
        raise HTTPException(404, 'Project not found')


@router.post("/projects/{project_id}/render", response_model=RenderStartResponse)
async def start_render(project_id: UUID, req: RenderStartRequest, user_id: str = Depends(get_supabase_user)):
    """Start a render job (draft or final)."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)

    # Check: 1 draft active per project
    if req.kind == 'draft':
        active = admin.table('render_jobs').select('id').eq('project_id', pid).eq('job_type', 'draft').in_('status', ['pending', 'running']).execute()
        if active.data:
            raise HTTPException(409, 'A draft render is already active for this project')

    # Verify timeline exists
    tl = admin.table('timelines').select('id').eq('id', str(req.timeline_id)).maybe_single().execute()
    if not tl.data:
        raise HTTPException(404, 'Timeline not found')

    job_res = admin.table('render_jobs').insert({
        'project_id': pid,
        'job_type': req.kind,
        'status': 'pending',
        'render_config': {'timeline_id': str(req.timeline_id), 'kind': req.kind},
    }).execute()

    if not job_res.data:
        raise HTTPException(500, 'Failed to create render job')

    job_id = str(job_res.data[0]['id'])

    # Enqueue Celery task
    try:
        from apps.worker.tasks.render_video import render_video
        render_video.delay(job_id)
    except Exception:
        pass

    return RenderStartResponse(render_job_id=UUID(job_id), job_type=req.kind)


@router.get("/jobs/{job_id}", response_model=RenderJobResponse)
async def get_render_job(job_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get render job status."""
    admin = get_supabase_admin()
    job = admin.table('render_jobs').select('*').eq('id', str(job_id)).maybe_single().execute()
    if not job.data:
        raise HTTPException(404, 'Render job not found')
    _verify_project_owner(admin, job.data['project_id'], user_id)
    return RenderJobResponse(**job.data)


@router.post("/jobs/{job_id}/cancel")
async def cancel_render_job(job_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Cancel a running render job."""
    admin = get_supabase_admin()
    job = admin.table('render_jobs').select('*').eq('id', str(job_id)).maybe_single().execute()
    if not job.data:
        raise HTTPException(404, 'Render job not found')
    _verify_project_owner(admin, job.data['project_id'], user_id)

    if job.data['status'] not in ('pending', 'running'):
        raise HTTPException(400, f'Cannot cancel job with status: {job.data["status"]}')

    admin.table('render_jobs').update({'cancel_requested': True}).eq('id', str(job_id)).execute()
    return {"status": "cancel_requested", "job_id": str(job_id)}


@router.get("/projects/{project_id}/exports", response_model=list[RenderJobResponse])
async def list_exports(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """List completed render jobs (exports) for a project."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_project_owner(admin, pid, user_id)

    jobs = admin.table('render_jobs').select('*').eq('project_id', pid).eq('status', 'success').order('finished_at', desc=True).execute()
    return [RenderJobResponse(**j) for j in (jobs.data or [])]
