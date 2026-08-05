"""Celery task for channel analysis."""
from celery import Celery
from apps.worker.progress_tracker import ProgressTracker
import os

celery_app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

@celery_app.task(bind=True)
def analyze_channel_task(self, job_id: str, channel_id: str):
    """Main analysis task."""
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )
    
    async def run():
        for output in ProgressTracker.OUTPUTS:
            await tracker.start(output)
        
        # Output 1-4
        await tracker.increment("output_1_metadata", 25)
        # ... do work ...
        await tracker.complete("output_1_metadata", {"result": "data"})
        
        # Output 5-7
        await tracker.complete("output_5_emotions", {"emotions": []})
        
        # Output 8-14
        await tracker.complete("output_8_hooks", {"hooks": []})
        
        return {"status": "completed"}
    
    import asyncio
    return asyncio.run(run())
