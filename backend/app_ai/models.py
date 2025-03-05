from django.db import models
import uuid


class StorePrompt(models.Model):
    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    title = models.CharField(max_length=128)
    prompt = models.TextField()
    etype = models.CharField(max_length=128, null=True, blank=True)
    level = models.IntegerField(default=0)
    freq = models.IntegerField(default=-1)
    info = models.JSONField(default=dict)
    created_time = models.DateTimeField("date created")
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "store_prompt"
        ordering = ["-created_time"]
