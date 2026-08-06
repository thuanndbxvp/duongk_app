"""
Celery task: ingest_comments — fetch comments via YouTube Data API.
Phase 06.
"""
import os
import asyncio
from datetime import datetime, timezone
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.comments_provider import YouTubeDataAPIProvider
from supabase import create_client


@celery_app.task(
    name='apps.worker.tasks.ingest_comments',
    bind=True,
    max_retries=3,
    acks_late=True,
)
def ingest_comments(self: Task, batch_id: str):
    """Fetch comments for a batch and persist."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    batch = supabase.table('comment_ingest_batches').select('*').eq('id', batch_id).single().execute()
    if not batch.data:
        return {"status": "error", "reason": "batch not found"}

    if batch.data.get('status') == 'success':
        return {"status": "skipped", "reason": "already_success"}

    supabase.table('comment_ingest_batches').update({
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
    }).eq('id', batch_id).execute()

    try:
        provider = YouTubeDataAPIProvider(
            api_key=os.environ.get('YOUTUBE_API_KEY', '')
        )

        async def _run():
            comments, next_token = await provider.fetch(batch.data['video_ids'])
            return comments, next_token

        comments, next_token = asyncio.run(_run())

        supabase.table('comment_ingest_batches').update({
            'status': 'success',
            'total_fetched': len(comments),
            'page_token': next_token,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', batch_id).execute()

        return {"status": "success", "total": len(comments)}

    except Exception as e:
        supabase.table('comment_ingest_batches').update({
            'status': 'failed',
            'error_message': str(e)[:500],
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', batch_id).execute()
        raise
