"""
FastAPI router for character lab — Phase 11.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.character_lab import (
    LabStartRequest, LabResponse,
    CharacterAnchorResponse, BackgroundAnchorResponse, CoverageReport,
)

router = APIRouter(prefix="/api/projects", tags=["CharacterLab"])


def _verify_owner(admin, project_id: str, user_id: str):
    p = admin.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).maybe_single().execute()
    if not p.data:
        raise HTTPException(404, 'Project not found')


@router.post("/{project_id}/lab/start", response_model=LabResponse)
async def start_lab(project_id: UUID, req: LabStartRequest, user_id: str = Depends(get_supabase_user)):
    """Start a character lab session for a project."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)

    # Check style bible version if provided
    bible_ver = None
    if req.style_bible_id:
        bible = admin.table('style_bibles').select('version').eq('id', str(req.style_bible_id)).maybe_single().execute()
        if bible.data:
            bible_ver = bible.data['version']

    existing = admin.table('character_lab_runs').select('*').eq('project_id', pid).maybe_single().execute()
    if existing.data:
        # Check if style bible version changed → supersede
        if bible_ver and existing.data.get('style_bible_version') != bible_ver:
            admin.table('character_lab_runs').update({'status': 'superseded'}).eq('id', existing.data['id']).execute()
        else:
            return LabResponse(**existing.data)

    lab = admin.table('character_lab_runs').insert({
        'project_id': pid,
        'style_bible_id': str(req.style_bible_id) if req.style_bible_id else None,
        'style_bible_version': bible_ver,
        'status': 'generating',
        'cost_estimate': 25,
    }).execute()

    if not lab.data:
        raise HTTPException(500, 'Failed to create lab')

    # Auto-generate candidates from scene characters
    scenes = admin.table('project_scenes').select('characters, background').eq('project_id', pid).execute()
    all_chars = set()
    all_bgs = set()
    for s in (scenes.data or []):
        for c in s.get('characters', []):
            if c:
                all_chars.add(c)
        bg = s.get('background', '')
        if bg:
            all_bgs.add(bg)

    from apps.worker.services.character_lab import generate_character_candidates
    import asyncio
    if all_chars:
        asyncio.create_task(generate_character_candidates(admin, UUID(lab.data[0]['id']), list(all_chars)))

    admin.table('character_lab_runs').update({'status': 'ready'}).eq('id', lab.data[0]['id']).execute()
    updated = admin.table('character_lab_runs').select('*').eq('id', lab.data[0]['id']).single().execute()
    return LabResponse(**updated.data)


@router.get("/{project_id}/lab/characters", response_model=list[CharacterAnchorResponse])
async def get_character_anchors(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    lab = admin.table('character_lab_runs').select('id').eq('project_id', pid).maybe_single().execute()
    if not lab.data:
        return []
    anchors = admin.table('character_anchors').select('*').eq('lab_run_id', lab.data['id']).execute()
    return [CharacterAnchorResponse(**a) for a in (anchors.data or [])]


@router.get("/{project_id}/lab/coverage", response_model=CoverageReport)
async def get_coverage(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)
    from apps.worker.services.character_lab import coverage_check
    result = await coverage_check(admin, UUID(pid))
    return CoverageReport(**result)


@router.post("/{project_id}/lab/approve")
async def approve_lab(project_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Approve lab session. Only if coverage = 100%."""
    admin = get_supabase_admin()
    pid = str(project_id)
    _verify_owner(admin, pid, user_id)

    from apps.worker.services.character_lab import coverage_check
    cov = await coverage_check(admin, UUID(pid))
    if cov['coverage_pct'] < 1.0:
        raise HTTPException(422, f"Coverage is {cov['coverage_pct']*100:.0f}%. All scenes need character anchors.")

    lab = admin.table('character_lab_runs').select('*').eq('project_id', pid).single().execute()
    admin.table('character_lab_runs').update({'status': 'approved'}).eq('id', lab.data['id']).execute()

    admin.table('lab_approval_evidence').insert({
        'lab_run_id': lab.data['id'],
        'approved_by': user_id,
        'coverage_pct': cov['coverage_pct'],
    }).execute()

    return {"status": "approved", "coverage_pct": cov['coverage_pct']}
