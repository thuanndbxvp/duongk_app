"""
Celery task: render_video — render video from timeline model.
Phase 04: Draft 720p / Final 1080p, progress, cancel, verify.
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.render_planner import compile_ffmpeg_args
from apps.worker.services.ffmpeg_runner import run_ffmpeg, kill_pid
from supabase import create_client


@celery_app.task(
    name='apps.worker.tasks.render_video',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def render_video(self: Task, render_job_id: str):
    """
    Render video from timeline.

    Steps:
    1. Load render_job + timeline
    2. Build FFmpeg args via RenderPlanner
    3. Run FFmpeg with progress + cancel
    4. Verify output via ffprobe
    5. Save output_asset_id
    """
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Load job
    job_res = supabase.table('render_jobs').select('*').eq('id', render_job_id).single().execute()
    if not job_res.data:
        return {"status": "error", "reason": "job not found"}

    job = job_res.data
    if job.get('status') in ('success', 'cancelled'):
        return {"status": "skipped", "reason": job['status']}

    # Mark running
    supabase.table('render_jobs').update({
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
    }).eq('id', render_job_id).execute()

    try:
        # Load timeline
        tl_id = job.get('render_config', {}).get('timeline_id', '')
        tl_res = supabase.table('timelines').select('*').eq('id', tl_id).single().execute()
        if not tl_res.data:
            raise RuntimeError('Timeline not found')

        timeline = tl_res.data.get('model', {})
        kind = job.get('job_type', 'draft')
        output_path = os.path.join(os.environ.get('TEMP', '/tmp'), f'render_{render_job_id}.mp4')

        # Build FFmpeg args
        argv = compile_ffmpeg_args(timeline, kind, output_path)
        total_dur = float(timeline.get('total_duration', 30))

        last_progress = 0.0

        def progress_cb(p: float):
            nonlocal last_progress
            last_progress = p
            supabase.table('render_jobs').update({
                'render_config': {**job.get('render_config', {}), 'progress': round(p, 4)}
            }).eq('id', render_job_id).execute()

        def cancel_check() -> bool:
            j = supabase.table('render_jobs').select('cancel_requested').eq('id', render_job_id).single().execute()
            return bool(j.data.get('cancel_requested')) if j.data else False

        # Run FFmpeg
        rc = run_ffmpeg(['-hide_banner', '-loglevel', 'error'] + argv, render_job_id, cancel_check, progress_cb, total_dur)

        if cancel_check():
            supabase.table('render_jobs').update({
                'status': 'cancelled',
                'finished_at': datetime.now(timezone.utc).isoformat(),
            }).eq('id', render_job_id).execute()
            # Clean up output
            if os.path.exists(output_path):
                os.remove(output_path)
            return {"status": "cancelled"}

        if rc != 0:
            raise RuntimeError(f'FFmpeg exited with code {rc}')

        # Verify output
        _verify_output(output_path)

        # Save as asset
        import hashlib
        with open(output_path, 'rb') as f:
            data = f.read()
            checksum = hashlib.sha256(data).hexdigest()
            size = len(data)

        storage_key = f'renders/{render_job_id}.mp4'

        asset_res = supabase.table('assets').insert({
            'owner_id': job.get('project_id'),  # project owner resolved at query time
            'source': 'upload',
            'storage_key': storage_key,
            'mime_type': 'video/mp4',
            'size_bytes': size,
            'checksum': checksum,
            'status': 'ready',
        }).execute()

        asset_id = asset_res.data[0]['id'] if asset_res.data else None

        supabase.table('render_jobs').update({
            'status': 'success',
            'output_asset_id': asset_id,
            'render_config': {**job.get('render_config', {}), 'progress': 1.0},
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', render_job_id).execute()

        return {"status": "success", "asset_id": asset_id}

    except Exception as e:
        supabase.table('render_jobs').update({
            'status': 'failed',
            'error_code': 'render_error',
            'error_message': str(e)[:500],
            'retry_count': job.get('retry_count', 0) + 1,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', render_job_id).execute()
        raise


def _verify_output(path: str):
    """Verify rendered output via ffprobe."""
    import subprocess
    try:
        info = json.loads(subprocess.check_output(
            ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
            timeout=30,
        ))
    except Exception as e:
        raise RuntimeError(f'ffprobe failed: {e}')

    streams = info.get('streams', [])
    if not streams:
        raise RuntimeError('no_streams')

    dur = float(info.get('format', {}).get('duration', 0))
    if dur < 1.0:
        raise RuntimeError(f'output too short: {dur}s')

    # Check video codec
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if not video_streams:
        raise RuntimeError('no_video_stream')
