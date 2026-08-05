# Sprint 3 Task Group 3: Script Generation - Skill Routing

## Allowed Commands
- ✅ Read, Write, StrReplace, Delete
- ✅ ReadLints, self-fix linter
- ✅ Import: openai, json, re

## Not Allowed
- ❌ Không đổi RAG service (Task Group 1)
- ❌ Không launch subagents
- ❌ Không deploy

## Patterns to Follow
```python
# OpenAI client
from openai import OpenAI
client = OpenAI()

# Celery task
from celery import Task
@celery_app.task(name='apps.worker.tasks.script_generate.run', bind=True)

# Progress tracker
from apps.worker.services.progress_tracker import ProgressTracker
tracker = ProgressTracker(supabase, job_id)
```

## Files to Create
- ✅ `supabase/migrations/0016_scripts.sql`
- ✅ `apps/worker/services/antislop_service.py`
- ✅ `apps/worker/tasks/script_generate.py`
- ✅ `apps/api/routers/scripts.py`
- ✅ `apps/worker/services/test_antislop_service.py`
