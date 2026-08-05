# Kiến trúc & Luồng xử lý (PLAN): Task 2.5 - Progress Granularity (D1)

## 1. Mục tiêu

Implement Progress Tracking với:
- `update_job_sub_progress` RPC (race-safe)
- `ProgressTracker` class cho worker
- Sub-progress cho 14 outputs

## 2. D1 FIX - Race-Safe RPC

**Vấn đề:** Concurrent updates có thể overwrite nhau.

**Giải pháp:** Dùng `jsonb_set` + `FOR UPDATE` lock.

```sql
-- supabase/migrations/0014_progress_sub.rpc.sql

-- D1 FIX: Race-safe sub_progress update
CREATE OR REPLACE FUNCTION update_job_sub_progress(
    p_job_id UUID,
    p_output_key TEXT,
    p_progress_value JSONB,
    p_is_complete BOOLEAN DEFAULT false
)
RETURNS VOID AS $$
DECLARE
    v_current JSONB;
    v_locked RECORD;
BEGIN
    -- Lock the row to prevent concurrent updates
    SELECT sub_progress INTO v_locked
    FROM jobs
    WHERE id = p_job_id
    FOR UPDATE;
    
    -- Get current sub_progress
    v_current := COALESCE(v_locked.sub_progress, '{}'::jsonb);
    
    -- Update specific key using jsonb_set
    v_current := jsonb_set(v_current, ARRAY[p_output_key], p_progress_value);
    
    -- Update jobs table
    UPDATE jobs
    SET 
        sub_progress = v_current,
        status = CASE 
            WHEN p_is_complete THEN status  -- Keep current status
            ELSE status
        END,
        updated_at = NOW()
    WHERE id = p_job_id;
    
    -- Log progress
    RAISE NOTICE 'Job % progress updated: %', p_job_id, p_output_key;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION update_job_sub_progress TO authenticated;
```

## 3. ProgressTracker Class

```python
# apps/worker/progress_tracker.py
import asyncio
from typing import Dict, Any, Optional
from supabase import AsyncClient

class ProgressTracker:
    """
    Track progress for 14 outputs in Celery worker.
    
    Usage:
        tracker = ProgressTracker(job_id)
        await tracker.start("output_1_metadata")
        # ... do work ...
        await tracker.update("output_1_metadata", {"status": "analyzing"})
        # ... more work ...
        await tracker.complete("output_1_metadata", {"result": data})
    """
    
    # 14 outputs
    OUTPUTS = [
        "output_1_metadata",      # Deterministic Layer
        "output_2_tags",
        "output_3_performance",
        "output_4_duration",
        "output_5_emotions",       # NLP Layer
        "output_6_pacing",
        "output_7_category",
        "output_8_hooks",          # LLM Layer
        "output_9_structure",
        "output_10_hook_strength",
        "output_11_mimic_rules",
        "output_12_insights",
        "output_13_ideas",         # Sprint 3
        "output_14_thumbnail"      # Vision
    ]
    
    def __init__(self, job_id: str, supabase_url: str, supabase_key: str):
        self.job_id = job_id
        self.supabase = AsyncClient(supabase_url, supabase_key)
        self._cache: Dict[str, Any] = {}
    
    async def start(self, output_key: str):
        """Mark output as started."""
        await self._update(output_key, {
            "status": "running",
            "started_at": str(datetime.now()),
            "progress": 0
        })
    
    async def update(self, output_key: str, data: Dict[str, Any]):
        """Update progress with data."""
        current = self._cache.get(output_key, {})
        progress = current.get("progress", 0)
        
        await self._update(output_key, {
            **current,
            **data,
            "progress": progress,
            "updated_at": str(datetime.now())
        })
    
    async def increment(self, output_key: str, by: float = 10):
        """Increment progress by percentage."""
        current = self._cache.get(output_key, {})
        progress = min(100, current.get("progress", 0) + by)
        
        await self._update(output_key, {
            **current,
            "progress": progress,
            "updated_at": str(datetime.now())
        })
    
    async def complete(self, output_key: str, result: Any):
        """Mark output as complete."""
        await self._update(output_key, {
            "status": "completed",
            "progress": 100,
            "completed_at": str(datetime.now()),
            "result": result
        }, is_complete=True)
    
    async def fail(self, output_key: str, error: str):
        """Mark output as failed."""
        await self._update(output_key, {
            "status": "failed",
            "error": error,
            "failed_at": str(datetime.now())
        })
    
    async def _update(
        self,
        output_key: str,
        data: Dict[str, Any],
        is_complete: bool = False
    ):
        """Update database via RPC."""
        self._cache[output_key] = data
        
        try:
            await self.supabase.rpc(
                'update_job_sub_progress',
                {
                    'p_job_id': self.job_id,
                    'p_output_key': output_key,
                    'p_progress_value': data,
                    'p_is_complete': is_complete
                }
            )
        except Exception as e:
            # Log but don't fail the task
            print(f"Failed to update progress: {e}")
    
    async def get_overall_progress(self) -> float:
        """Calculate overall progress (0-100)."""
        if not self._cache:
            return 0
        
        completed = sum(1 for k, v in self._cache.items() if v.get("status") == "completed")
        running = sum(1 for k, v in self._cache.items() if v.get("status") == "running")
        
        # Completed = 100%, Running = partial (use stored progress)
        running_progress = sum(v.get("progress", 0) for v in self._cache.values() if v.get("status") == "running")
        
        total = completed * 100 + running_progress
        max_possible = len(self.OUTPUTS) * 100
        
        return total / max_possible * 100 if max_possible > 0 else 0
```

## 4. Integration with Celery Task

```python
# apps/worker/tasks/analysis_task.py
from celery import Task
from apps.worker.progress_tracker import ProgressTracker
from apps.worker.ml_models import get_pbhart_singleton

@celery.task(bind=True)
def analyze_channel_task(self, job_id: str, channel_id: str):
    """
    Celery task for channel analysis (14 outputs).
    """
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ['SUPABASE_URL'],
        supabase_key=os.environ['SUPABASE_SERVICE_ROLE_KEY']
    )
    
    try:
        # Start tracking all outputs
        for output in ProgressTracker.OUTPUTS:
            await tracker.start(output)
        
        # ===== DETERMINISTIC LAYER =====
        await tracker.increment("output_1_metadata", 25)
        
        # Fetch videos
        videos = await youtube_collector.collect(channel_id)
        await tracker.update("output_1_metadata", {"videos_collected": len(videos)})
        
        # Generate Output 1-4
        metadata = generate_metadata_analysis(videos)
        await tracker.complete("output_1_metadata", metadata)
        
        # ... similar for output 2, 3, 4 ...
        
        # ===== NLP LAYER =====
        # Load ML models as singletons (E2)
        model = get_pbhart_singleton()
        
        # Output 5-7
        emotions = analyze_emotions(videos)
        await tracker.complete("output_5_emotions", emotions)
        
        # ... etc ...
        
        # ===== LLM LAYER =====
        # Output 8-11, 14
        hooks = await llm.analyze_hooks(videos)
        await tracker.complete("output_8_hooks", hooks)
        
        # ... etc ...
        
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        await tracker.fail("current_output", str(e))
        raise
```

## 5. Database Schema

```sql
-- jobs table already has sub_progress column (from Sprint 1)
-- Just need to ensure the RPC works

-- Verify column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'sub_progress';
```

## 6. Dependencies

```bash
pip install supabase-py
```

## 7. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/worker/progress_tracker.py` | ProgressTracker class |
| `apps/worker/tasks/analysis_task.py` | Celery task example |
| `supabase/migrations/0014_progress_sub.rpc.sql` | D1 RPC |

## 8. Verification

- [ ] RPC handles concurrent updates
- [ ] FOR UPDATE lock prevents race conditions
- [ ] Progress updates reflect in DB
- [ ] Overall progress calculation correct
- [ ] Task updates progress as it runs
- [ ] Error handling works
