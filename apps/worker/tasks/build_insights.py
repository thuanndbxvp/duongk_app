"""
Celery task: build_insights — cluster comments + generate insight items.
Phase 06.
"""
import os
import asyncio
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.insights_service import cluster_comments, build_insight_from_cluster
from supabase import create_client


@celery_app.task(
    name='apps.worker.tasks.build_insights',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def build_insights(self: Task, assistant_id: str):
    """Cluster comments and build evidence-backed insights."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get recent comment batches for this assistant
    batches = supabase.table('comment_ingest_batches').select('*').eq('channel_assistant_id', assistant_id).eq('status', 'success').order('created_at', desc=True).limit(5).execute()

    if not batches.data:
        return {"status": "skipped", "reason": "no_comment_data"}

    # Mock comments from batches (in production: load from normalized store)
    comments = []
    for batch in batches.data:
        for j in range(batch.get('total_fetched', 0)):
            comments.append({
                'comment_id': f"c-{batch['id']}-{j}",
                'text': f"Mock insight comment {j} about various topics like quality, pacing, content ideas",
                'like_count': j % 10,
            })

    # Cluster
    clusters = cluster_comments(comments)
    if not clusters:
        return {"status": "skipped", "reason": "no_clusters"}

    # Build insights
    created = 0
    for cluster in clusters:
        insight = build_insight_from_cluster(cluster, assistant_id)
        if not insight:
            continue

        supabase.table('insight_items').insert({
            'channel_assistant_id': assistant_id,
            'title': insight['title'],
            'body': insight['body'],
            'evidence_comment_ids': insight['evidence_comment_ids'],
            'opportunity_score': insight['opportunity_score'],
            'status': 'pending',
        }).execute()
        created += 1

    return {"status": "completed", "clusters": len(clusters), "insights_created": created}
