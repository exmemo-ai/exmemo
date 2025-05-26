from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class UserTask(models.Model):
    TASK_STATUS = (
        ('PENDING', 'Pending'),
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failed'),
        ('REVOKED', 'Revoked'),
    )

    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    task_id = models.CharField(max_length=255, unique=True)
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=TASK_STATUS, default='PENDING')
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    result = models.JSONField(null=True, blank=True)
    progress = models.FloatField(default=0, help_text="task progress 0-100")

    class Meta:
        db_table = "store_user_task"
        ordering = ["-created_time"]
