# Sprint 3 Task Group 2: Idea Generation - Skill Routing

## Commands/Tools ĐƯỢC PHÉP

### File Operations
- ✅ `Read` - Đọc existing files
- ✅ `Write` - Tạo file mới
- ✅ `StrReplace` - Sửa file
- ✅ `Delete` - Xóa test files thừa

### Code Quality
- ✅ `ReadLints` - Check linter
- ✅ Tự fix linter errors

### Dependencies
- ✅ Import từ `apps.worker.services.*`
- ✅ Import `hdbscan`, `sklearn`, `numpy`
- ✅ Import `supabase` client

---

## Commands/Tools KHÔNG ĐƯỢC PHÉP

- ❌ Không tạo migration thay đổi tables Sprint 2
- ❌ Không launch subagents
- ❌ Không dùng `Shell` để deploy

---

## Skills BẮT BUỘC

### Python ML Patterns
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from hdbscan import HDBSCAN
import numpy as np
```

### Supabase Pattern
```python
from apps.worker.services.supabase_admin import get_supabase_admin
admin = get_supabase_admin()
result = admin.table('channel_deep_analysis').select('*').eq('assistant_id', ...).execute()
```

### Celery Task Pattern
```python
from celery import Task
from apps.worker.celery_app import celery_app

@celery_app.task(name='apps.worker.tasks.idea_generate.run', bind=True, max_retries=2)
def run(self: Task, job_id: str, assistant_id: str):
    ...
```

---

## File Paths Tuyệt Đối Không Sửa

- ❌ `apps/worker/services/supabase_admin.py`
- ❌ `supabase/migrations/0001` đến `0014`
- ❌ `apps/worker/services/rag_service.py` (Task Group 1)

---

## File Paths Có Thể Tạo

- ✅ `supabase/migrations/0015_ideas.sql`
- ✅ `apps/worker/services/idea_generator.py`
- ✅ `apps/worker/tasks/idea_generate.py`
- ✅ `apps/worker/services/test_idea_generator.py`
