# Quy trình thực thi chi tiết (MSEW): Task 1.2 - Thiết lập Infrastructure (Docker & Observability)

## BƯỚC 1: Tạo .env.example
Tạo file ở thư mục gốc:
```env
YOUTUBE_API_KEY_1=...
OPENAI_API_KEY=...
COHERE_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
SENTRY_DSN=...
```

## BƯỚC 2: Tạo docker-compose.yml
Cấu hình 4 worker chuẩn E2:
```yaml
services:
  worker_ml:
    command: celery -A apps.worker.celery_app worker -Q ml_queue --concurrency=2
    environment:
      - CELERYD_MAX_TASKS_PER_CHILD=50
  worker_high:
    command: celery -A apps.worker.celery_app worker -Q high_queue --concurrency=4
  worker_io:
    command: celery -A apps.worker.celery_app worker -Q io_queue --concurrency=8
  worker_normal:
    command: celery -A apps.worker.celery_app worker -Q normal_queue --concurrency=4
```

## BƯỚC 3: Main FastAPI (apps/api/main.py)
```python
from fastapi import FastAPI
import sentry_sdk
import os

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
app = FastAPI(title="YouTube AI SaaS")
```
