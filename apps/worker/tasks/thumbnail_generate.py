"""
Celery task: thumbnail_generate — AI thumbnail candidates.
Phase 05: 3-5 candidates 1280x720 from Gemini/Nano Banana.
"""
import os
import hashlib
import asyncio
from celery import Task
from apps.worker.celery_app import celery_app
from supabase import create_client


@celery_app.task(
    name='apps.worker.tasks.thumbnail_generate',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def thumbnail_generate(self: Task, project_id: str, provider: str = "gemini", count: int = 3):
    """Generate thumbnail candidates for a project."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get project + brief
    proj = supabase.table('projects').select('*').eq('id', project_id).single().execute()
    if not proj.data:
        return {"status": "error", "reason": "project not found"}

    brief = supabase.table('project_briefs').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    topic = brief.data[0].get('topic', '') if brief.data else 'video thumbnail'

    # Generate candidates (stub: create placeholder assets)
    candidates = []
    for i in range(count):
        cid = f"thumb-{project_id}-{i+1}"
        checksum = hashlib.sha256(cid.encode()).hexdigest()
        storage_key = f"thumbnails/{project_id}/candidate_{i+1}.png"

        asset_res = supabase.table('assets').insert({
            'owner_id': proj.data['user_id'],
            'source': provider,
            'provider_id': cid,
            'storage_key': storage_key,
            'mime_type': 'image/png',
            'size_bytes': 204800,
            'checksum': checksum,
            'width': 1280,
            'height': 720,
            'status': 'ready',
            'license': {'provider': provider, 'generated_for': topic},
        }).execute()

        if asset_res.data:
            asset_id = asset_res.data[0]['id']
            score = 0.7 + (i * 0.1)  # Mock scoring
            supabase.table('thumbnail_candidates').insert({
                'project_id': project_id,
                'asset_id': asset_id,
                'score': min(score, 1.0),
                'provider': provider,
            }).execute()
            candidates.append({"asset_id": asset_id, "score": score})

    return {"status": "generated", "candidates": len(candidates), "project_id": project_id}
