"""
Celery task for scene breakdown.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.scene_breaker import SceneBreaker
from apps.worker.progress_tracker import ProgressTracker
from supabase import create_client
from openai import OpenAI
import json
import os
import asyncio


@celery_app.task(
    name='apps.worker.tasks.scene_breakdown.run',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def run(self: Task, job_id: str, script_data: dict, assistant_id: str) -> dict:
    """
    Break script into scenes with B-roll data.
    
    Args:
        job_id: Job UUID
        script_data: Script JSON from Task Group 3
        assistant_id: Channel assistant UUID
        
    Returns:
        dict with scenes array
    """
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    async def _run():
        try:
            # === FETCH CHANNEL PACING ===
            await tracker.start('fetch_pacing')

            assistant = supabase.table('channel_assistants').select('pacing_profile').eq('id', assistant_id).single().execute()
            pacing_wpm = assistant.data.get('pacing_profile', {}).get('wpm', 150) if assistant.data else 150

            await tracker.complete('fetch_pacing', {"status": "done"})

            # === SEGMENT SCENES ===
            await tracker.start('segment_scenes')

            breaker = SceneBreaker(default_wpm=pacing_wpm)

            # Get script text
            script_text = script_data.get('body', script_data.get('script_text', ''))
            target_duration = script_data.get('estimated_duration_minutes', 10)

            scenes = breaker.segment_scenes(
                script_text=script_text,
                pacing_wpm=pacing_wpm,
                target_duration_minutes=target_duration,
            )

            await tracker.complete('segment_scenes', {"status": "done"})

            # === TRANSLATE B-ROLL KEYWORDS ===
            await tracker.start('broll_translation')

            all_keywords = []
            for scene in scenes:
                all_keywords.extend(scene.get('broll_keywords', []))

            if all_keywords:
                openai = OpenAI()
                translations = await breaker.translate_broll_keywords(all_keywords, openai)

                # Map translations back to scenes
                translation_map = {t.get('vn'): t for t in translations if isinstance(t, dict) and 'vn' in t}
                for scene in scenes:
                    scene['broll_translations'] = [
                        translation_map[kw]
                        for kw in scene.get('broll_keywords', [])
                        if kw in translation_map
                    ]
            else:
                for scene in scenes:
                    scene['broll_translations'] = []

            await tracker.complete('broll_translation', {"status": "done"})

            # === SAVE RESULTS ===
            stats = breaker.calculate_total_duration(scenes)
            result = {
                'scenes': scenes,
                **stats,
            }

            supabase.table('jobs').update({
                'status': 'completed',
                'progress': 100,
                'result_payload': result,
                'sub_progress': tracker._cache,
            }).eq('id', job_id).execute()

            # Update generated_scripts with scenes
            supabase.table('generated_scripts').update({
                'scenes': scenes,
            }).eq('job_id', job_id).execute()

            return result

        except Exception as e:
            await tracker.fail('scene_breakdown', str(e))
            supabase.table('jobs').update({
                'status': 'failed',
                'error_message': str(e),
            }).eq('id', job_id).execute()
            raise
            
    return asyncio.run(_run())
