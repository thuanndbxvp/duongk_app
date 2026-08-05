# MSEW: Task 2.5 - Progress Granularity

> Prerequisites: `pip install supabase-py celery`

---

## Micro-Steps

### Step 1: Race-Safe RPC (D1 FIX)
**File:** `supabase/migrations/0014_progress_sub.rpc.sql`

```sql
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
BEGIN
    -- Lock row to prevent concurrent updates
    SELECT sub_progress INTO v_current
    FROM jobs
    WHERE id = p_job_id
    FOR UPDATE;
    
    -- Get current or init
    v_current := COALESCE(v_current, '{}'::jsonb);
    
    -- Update specific key
    v_current := jsonb_set(v_current, ARRAY[p_output_key], p_progress_value);
    
    -- Update jobs table
    UPDATE jobs SET sub_progress = v_current, updated_at = NOW() WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION update_job_sub_progress TO authenticated;
```

---

### Step 2: ProgressTracker Class
**File:** `apps/worker/progress_tracker.py`

```python
"""ProgressTracker for 14 outputs."""
from typing import Dict, Any, Optional
from datetime import datetime

class ProgressTracker:
    OUTPUTS = [
        "output_1_metadata", "output_2_tags", "output_3_performance", "output_4_duration",
        "output_5_emotions", "output_6_pacing", "output_7_category",
        "output_8_hooks", "output_9_structure", "output_10_hook_strength", "output_11_mimic_rules",
        "output_12_insights", "output_13_ideas", "output_14_thumbnail"
    ]
    
    def __init__(self, job_id: str, supabase_url: str, supabase_key: str):
        self.job_id = job_id
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self._cache: Dict[str, Any] = {}
    
    async def start(self, output_key: str):
        """Mark output as started."""
        await self._update(output_key, {"status": "running", "progress": 0, "started_at": str(datetime.now())})
    
    async def update(self, output_key: str, data: Dict[str, Any]):
        """Update progress with data."""
        current = self._cache.get(output_key, {})
        progress = current.get("progress", 0)
        await self._update(output_key, {**current, **data, "progress": progress})
    
    async def increment(self, output_key: str, by: float = 10):
        """Increment progress."""
        current = self._cache.get(output_key, {})
        progress = min(100, current.get("progress", 0) + by)
        await self._update(output_key, {**current, "progress": progress})
    
    async def complete(self, output_key: str, result: Any):
        """Mark output as complete."""
        await self._update(output_key, {"status": "completed", "progress": 100, "result": result, "completed_at": str(datetime.now())}, is_complete=True)
    
    async def fail(self, output_key: str, error: str):
        """Mark output as failed."""
        await self._update(output_key, {"status": "failed", "error": error})
    
    async def _update(self, output_key: str, data: Dict[str, Any], is_complete: bool = False):
        """Update database via RPC."""
        self._cache[output_key] = data
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.supabase_url}/rest/v1/rpc/update_job_sub_progress",
                    headers={"apikey": self.supabase_key, "Authorization": f"Bearer {self.supabase_key}"},
                    json={"p_job_id": self.job_id, "p_output_key": output_key, "p_progress_value": data, "p_is_complete": is_complete}
                )
        except Exception as e:
            print(f"Progress update failed: {e}")
```

---

### Step 3: Celery Task Example
**File:** `apps/worker/tasks/analysis_task.py`

```python
"""Celery task for channel analysis."""
from celery import Celery
from apps.worker.progress_tracker import ProgressTracker

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task(bind=True)
def analyze_channel_task(self, job_id: str, channel_id: str):
    """Main analysis task."""
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url='https://xxx.supabase.co',
        supabase_key='xxx'
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
```

---

### Step 4: Unit Tests
**File:** `tests/test_progress/test_tracker.py`

```python
import pytest
from apps.worker.progress_tracker import ProgressTracker

def test_tracker_initialization():
    tracker = ProgressTracker("job123", "http://localhost", "key")
    assert tracker.job_id == "job123"
    assert len(ProgressTracker.OUTPUTS) == 14
```

---

**Verify:** `pytest tests/test_progress/ -v`
