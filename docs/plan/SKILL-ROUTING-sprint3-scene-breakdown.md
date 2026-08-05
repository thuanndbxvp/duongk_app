# Sprint 3 Task Group 4: Scene Breakdown - Skill Routing

## Allowed Commands
- ✅ Read, Write, StrReplace, Delete
- ✅ ReadLints, self-fix linter
- ✅ Import: openai, json, re

## Not Allowed
- ❌ Không đổi Task Group 3 files
- ❌ Không tạo migration mới
- ❌ Không launch subagents

## Patterns
```python
# SceneBreaker class
class SceneBreaker:
    def segment_scenes(self, script_text: str, wpm: int = 150) -> list[dict]:
        ...
    def _extract_broll_keywords(self, text: str) -> list[str]:
        ...

# Celery task
@celery_app.task(name='apps.worker.tasks.scene_breakdown.run', bind=True)
async def run(self, job_id: str, script_data: dict, assistant_id: str):
    ...

# Update existing table (no new migration)
supabase.table('generated_scripts').update({'scenes': scenes}).eq('job_id', job_id).execute()
```

## Files to Create
- ✅ `apps/worker/services/scene_breaker.py`
- ✅ `apps/worker/tasks/scene_breakdown.py`
- ✅ `apps/api/routers/scripts.py` (update - add endpoint)
- ✅ `apps/worker/services/test_scene_breaker.py`
