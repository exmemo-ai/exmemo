from django.db import models
import uuid

class StoreMessage(models.Model):
    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    sender = models.CharField(max_length=64, null=True, blank=True)
    receiver = models.CharField(max_length=64, null=True, blank=True)
    rtype = models.CharField(max_length=32, null=True, blank=True)
    sid = models.CharField(max_length=64, null=True, blank=True)
    sname = models.CharField(max_length=128, null=True, blank=True)
    is_group = models.BooleanField(default=False)
    content = models.TextField()
    meta = models.JSONField(default=dict)
    source = models.CharField(max_length=32, null=True, blank=True)
    created_time = models.DateTimeField("date created")

    def __str__(self):
        return self.title

    class Meta:
        db_table = "store_message"
        ordering = ["-created_time"]