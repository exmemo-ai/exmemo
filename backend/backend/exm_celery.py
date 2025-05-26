import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('exmemo')

redis_host = os.environ.get('REDIS_HOST', settings.BACKEND_ADDR_OUTER)
redis_port = os.environ.get('REDIS_PORT', '6379')

app.conf.update(
    broker_url=f'redis://{redis_host}:{redis_port}/0',
    result_backend=f'redis://{redis_host}:{redis_port}/1',
    task_serializer='json',
    accept_content=['json'],
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    }
)

app.autodiscover_tasks()