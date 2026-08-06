"""
Celery task: metadata_package — build YouTube metadata.
Phase 05: Title, description, tags, chapters, hashtags.
"""
import os
import asyncio
from celery import Task
from apps.worker.celery_app import celery_app
from supabase import create_client


@celery_app.task(
    name='apps.worker.tasks.metadata_package',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def metadata_package(self: Task, project_id: str):
    """Build metadata package for project export."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get brief
    brief = supabase.table('project_briefs').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    if not brief.data:
        return {"status": "error", "reason": "no brief"}

    b = brief.data[0]
    topic = b.get('topic', '')

    # Get selected thumbnail
    thumb = supabase.table('thumbnail_candidates').select('*').eq('project_id', project_id).eq('selected', True).maybe_single().execute()

    # Get SRT
    srt = supabase.table('subtitle_tracks').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()

    # Build metadata
    title = f"{topic} — AppDK"
    description = f"Video này được tạo tự động bởi AppDK.\n\nChủ đề: {topic}\nĐối tượng: {b.get('audience', '')}"
    tags = [topic, b.get('audience', ''), b.get('tone', ''), 'appdk', 'ai generated']
    hashtags = ["#appdk", "#ai", "#youtube"]

    # Get next version
    latest = supabase.table('project_exports').select('version').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    next_ver = (latest.data[0]['version'] + 1) if latest.data else 1

    export = supabase.table('project_exports').insert({
        'project_id': project_id,
        'version': next_ver,
        'title': title,
        'description': description,
        'tags': tags,
        'hashtags': hashtags,
        'thumbnail_asset_id': thumb.data['asset_id'] if thumb.data else None,
        'srt_track_id': srt.data[0]['id'] if srt.data else None,
        'metadata': {
            'topic': topic,
            'language': b.get('language', 'vi'),
            'aspect_ratio': b.get('aspect_ratio', '9:16'),
        },
    }).execute()

    data = export.data[0] if export.data else {}
    return {"status": "built", "export_id": data.get('id'), "title": title}
