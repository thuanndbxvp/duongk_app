"""
FastAPI router for channel intelligence — FIXED: No Celery imports
All async tasks now use FastAPI BackgroundTasks
Prefix: /api
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.channel_intel import (
    InsightItemResponse, InsightApproveRequest,
    InsightToProjectResponse, IngestCommentsRequest,
    IngestCommentsResponse,
)


router = APIRouter(prefix="/api", tags=["ChannelIntel"])


# =============================================================================
# Helper
# =============================================================================

def _verify_assistant_owner(admin, assistant_id: str, user_id: str):
    ca = admin.table('channel_assistants').select('id').eq('id', assistant_id).eq('user_id', user_id).maybe_single().execute()
    if not ca.data:
        raise HTTPException(404, 'Assistant not found')


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _ingest_comments_async(batch_id: str):
    """
    Async task to ingest comments.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        db.table('comment_ingest_batches').update({
            'status': 'running',
        }).eq('id', batch_id).execute()
        
        # Placeholder: implement actual comment ingestion
        
        db.table('comment_ingest_batches').update({
            'status': 'completed',
        }).eq('id', batch_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[channel_intel] Comment ingestion failed for {batch_id}: {e}")
        
        db.table('comment_ingest_batches').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', batch_id).execute()


# =============================================================================
# Routes
# =============================================================================

@router.post("/assistants/{assistant_id}/ingest", response_model=IngestCommentsResponse)
async def ingest_comments(
    assistant_id: UUID,
    req: IngestCommentsRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Ingest comments for assistant's videos."""
    admin = get_supabase_admin()
    aid = str(assistant_id)
    _verify_assistant_owner(admin, aid, user_id)

    batch = admin.table('comment_ingest_batches').insert({
        'channel_assistant_id': aid,
        'video_ids': req.video_ids,
        'status': 'pending',
    }).execute()

    if not batch.data:
        raise HTTPException(500, 'Failed to create batch')

    batch_id = str(batch.data[0]['id'])

    # Queue via BackgroundTasks
    background_tasks.add_task(_ingest_comments_async, batch_id)

    return IngestCommentsResponse(batch_id=UUID(batch_id), video_count=len(req.video_ids), status='enqueued')


@router.get("/assistants/{assistant_id}/insights", response_model=list[InsightItemResponse])
async def get_insights(assistant_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get all insights for an assistant."""
    admin = get_supabase_admin()
    aid = str(assistant_id)
    _verify_assistant_owner(admin, aid, user_id)

    insights = admin.table('insight_items').select('*').eq('channel_assistant_id', aid).order('created_at', desc=True).execute()
    return [InsightItemResponse(**i) for i in (insights.data or [])]


@router.post("/insights/{insight_id}/approve")
async def approve_insight(insight_id: UUID, req: InsightApproveRequest, user_id: str = Depends(get_supabase_user)):
    """Approve or reject an insight."""
    admin = get_supabase_admin()
    iid = str(insight_id)

    insight = admin.table('insight_items').select('*').eq('id', iid).single().execute()
    if not insight.data:
        raise HTTPException(404, 'Insight not found')

    _verify_assistant_owner(admin, insight.data['channel_assistant_id'], user_id)

    if req.decision == 'approved':
        admin.table('insight_items').update({'status': 'approved'}).eq('id', iid).execute()
        admin.table('insight_outcomes').insert({
            'insight_id': iid,
            'outcome_type': 'approved_by_user',
            'metadata': {'user_id': user_id},
        }).execute()
    else:
        admin.table('insight_items').update({'status': 'rejected'}).eq('id', iid).execute()

    return {"status": req.decision, "insight_id": iid}


@router.post("/insights/{insight_id}/to-project", response_model=InsightToProjectResponse)
async def insight_to_project(insight_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Convert an approved insight into a new project."""
    admin = get_supabase_admin()
    iid = str(insight_id)

    insight = admin.table('insight_items').select('*').eq('id', iid).single().execute()
    if not insight.data:
        raise HTTPException(404, 'Insight not found')

    if insight.data['status'] != 'approved':
        raise HTTPException(400, 'Insight must be approved first')

    _verify_assistant_owner(admin, insight.data['channel_assistant_id'], user_id)

    import hashlib
    brief_topic = insight.data['title']
    brief_hash = hashlib.sha256(brief_topic.encode()).hexdigest()

    project_res = admin.table('projects').insert({
        'user_id': user_id,
        'channel_assistant_id': insight.data['channel_assistant_id'],
        'mode': 'clone_channel',
        'status': 'draft',
        'approval_state': 'draft',
        'brief_hash': brief_hash,
    }).execute()

    project_id = project_res.data[0]['id']

    admin.table('project_briefs').insert({
        'project_id': project_id,
        'version': 1,
        'topic': brief_topic,
        'audience': 'general',
        'language': 'vi',
    }).execute()

    admin.table('insight_items').update({
        'status': 'applied',
        'source_project_id': project_id,
    }).eq('id', iid).execute()

    admin.table('insight_outcomes').insert({
        'insight_id': iid,
        'project_id': project_id,
        'outcome_type': 'project_created',
    }).execute()

    return InsightToProjectResponse(insight_id=insight_id, project_id=UUID(project_id), status='created')
