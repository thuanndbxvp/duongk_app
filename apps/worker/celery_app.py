import os
import logging
from celery import Celery

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Celery
# Fallback to local redis if env vars are not set
redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    'youtube_ai_worker',
    broker=redis_url,
    backend=result_backend
)

celery_app.conf.update(
    task_default_queue='normal_queue',
    task_routes={
        # Map tasks to specific queues based on PRD requirements
        'apps.worker.tasks.ml.*': {'queue': 'ml_queue'},
        'apps.worker.tasks.high.*': {'queue': 'high_queue'},
        'apps.worker.tasks.io.*': {'queue': 'io_queue'},
        'apps.worker.tasks.normal.*': {'queue': 'normal_queue'},
    }
)

# Auto-discover tasks in the worker directory
celery_app.autodiscover_tasks(['apps.worker.tasks'])
