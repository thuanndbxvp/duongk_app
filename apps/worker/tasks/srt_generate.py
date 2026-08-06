"""
Celery task: srt_generate — build SRT from voice_lines.
Phase 03.
"""
import os
from celery import Task
from apps.worker.celery_app import celery_app
from supabase import create_client


def sec_to_srt(seconds: float) -> str:
    """Convert float seconds to SRT timestamp: HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(voice_lines: list[dict]) -> str:
    """Build SRT content from ordered voice_lines."""
    blocks = []
    cursor = 0.0
    for line in voice_lines:
        dur = float(line.get('duration_seconds') or 0)
        if dur <= 0:
            dur = 3.0  # fallback
        start = cursor
        end = start + dur
        idx = len(blocks) + 1
        blocks.append(f"{idx}\n{sec_to_srt(start)} --> {sec_to_srt(end)}\n{line.get('text', '')}\n")
        cursor = end
    return "\n".join(blocks)


@celery_app.task(
    name='apps.worker.tasks.srt_generate',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def srt_generate(self: Task, project_id: str):
    """Generate SRT file for a project from voice_lines."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Get all voice_lines for project via scenes
    scenes = supabase.table('project_scenes').select('id').eq('project_id', project_id).execute()
    if not scenes.data:
        return {"status": "no_scenes"}

    scene_ids = [s['id'] for s in scenes.data]
    lines_res = supabase.table('voice_lines').select('*').in_('scene_id', scene_ids).order('created_at').execute()

    voice_lines = lines_res.data or []
    if not voice_lines:
        return {"status": "no_voice_lines"}

    srt_content = build_srt(voice_lines)
    storage_key = f"srt/{project_id}/subtitle_v1.srt"

    # Get next version
    latest = supabase.table('subtitle_tracks').select('version').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    next_ver = (latest.data[0]['version'] + 1) if latest.data else 1

    supabase.table('subtitle_tracks').insert({
        'project_id': project_id,
        'format': 'srt',
        'storage_key': storage_key,
        'version': next_ver,
        'status': 'generated',
    }).execute()

    return {"status": "generated", "storage_key": storage_key, "version": next_ver}
