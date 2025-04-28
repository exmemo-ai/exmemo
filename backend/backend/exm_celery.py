import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('exmemo')

app.conf.update(
    broker_url=f'redis://{settings.BACKEND_ADDR_OUTER}:6379/0',
    result_backend=f'redis://{settings.BACKEND_ADDR_OUTER}:6379/1',
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