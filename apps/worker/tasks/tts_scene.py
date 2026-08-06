"""
Celery task: tts_scene — synthesize voice for a single scene.
Phase 03: Idempotent by (scene_id, voice_version).
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from celery import Task
from apps.worker.celery_app import celery_app
from supabase import create_client
from apps.worker.services.omnivoice_client import clone_voice_async

TTS_TIMEOUT_SECONDS = 60


@celery_app.task(
    name='apps.worker.tasks.tts_scene',
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def tts_scene(self: Task, voice_line_id: str):
    """
    Synthesize TTS audio for a voice_line.
    Idempotent: if already 'success', skip.
    """
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Fetch voice_line
    line = supabase.table('voice_lines').select('*').eq('id', voice_line_id).single().execute()
    if not line.data:
        return {"status": "error", "reason": "voice_line not found"}

    row = line.data
    if row.get('status') == 'success':
        return {"status": "skipped", "reason": "already_success"}

    # Mark running
    supabase.table('voice_lines').update({
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
    }).eq('id', voice_line_id).execute()

    try:
        # Get voice profile for reference audio
        voice_profile = None
        if row.get('voice_profile_id'):
            vp = supabase.table('voice_profiles').select('*').eq('id', row['voice_profile_id']).maybe_single().execute()
            if vp.data:
                voice_profile = vp.data

        # Determine reference audio URL
        ref_audio_url = voice_profile.get('sample_audio_url') if voice_profile else None
        storage_key = f"tts/{row['scene_id']}_v{row['voice_version']}.wav"

        # Call TTS (try local OmniVoice first, then Modal fallback)
        text = row.get('text', '')
        duration = _synthesize_local(text, ref_audio_url, storage_key)

        if duration is None:
            # Fallback to Modal
            clone_voice_async(text=text, reference_audio_url=ref_audio_url or '', output_key=storage_key)
            duration = _estimate_duration_from_text(text)

        # Update voice_line
        supabase.table('voice_lines').update({
            'status': 'success',
            'storage_key': storage_key,
            'duration_seconds': duration,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', voice_line_id).execute()

        # Update project_scenes actual_duration if needed
        supabase.table('project_scenes').update({
            'estimated_duration': duration,
        }).eq('id', row['scene_id']).execute()

        return {"status": "success", "duration": duration}

    except Exception as e:
        supabase.table('voice_lines').update({
            'status': 'failed',
            'error_code': 'tts_error',
            'error_message': str(e)[:500],
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', voice_line_id).execute()
        raise


def _synthesize_local(text: str, ref_audio_url: str | None, output_key: str) -> float | None:
    """Try local OmniVoice server. Returns duration_seconds or None."""
    import urllib.request
    try:
        req = urllib.request.Request(
            'http://localhost:8001/synthesize',
            data=json.dumps({
                'text': text,
                'reference_audio_url': ref_audio_url or '',
                'output_key': output_key,
            }).encode(),
            headers={'Content-Type': 'application/json'},
        )
        resp = urllib.request.urlopen(req, timeout=TTS_TIMEOUT_SECONDS)
        data = json.loads(resp.read())
        return float(data.get('duration_seconds', 0))
    except Exception:
        return None


def _estimate_duration_from_text(text: str) -> float:
    """Rough WPM estimate (fallback). ~150 WPM → 2.5 words/sec."""
    words = len(text.split())
    return round(words / 2.5, 2)
