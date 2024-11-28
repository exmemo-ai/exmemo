from django.db import models
from pgvector.django import VectorField
import uuid


class StoreEntry(models.Model):
    class EntryType(models.TextChoices):
        RECORD = "record"  # Single Record
        NOTE = "note"  # Notes, usually are text
        FILE = "file"  # Files
        WEB = "web"  # Web Pages
        CHAT = "chat" # Chat Records

    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)

    embeddings = VectorField(dimensions=None, default=None, null=True)
    emb_model = models.CharField(max_length=64, null=True, blank=True)
    block_id = models.IntegerField(default=0)
    raw = models.TextField(null=True, blank=True)
    #
    title = models.CharField(max_length=256, default=None, null=True, blank=True)
    meta = models.JSONField(default=dict)
    #
    etype = models.CharField(
        max_length=30, choices=EntryType.choices, default=EntryType.NOTE
    )
    # add
    atype = models.CharField(
        max_length=32, null=True, blank=True
    )  # Record Qualitative: subjective, objective, third_party
    ctype = models.CharField(
        max_length=64, null=True, blank=True
    )  # Content type, e.g.: Technology, Literature, History
    status = models.CharField(max_length=64, default="init")  # collect, todo
    source = models.CharField(
        max_length=32, default=None, null=True, blank=True
    )  # wechat,frontend,obsidian,web_chrome_bm
    access_level = models.IntegerField(default=-1)  # confidentiality level
    #
    addr = models.URLField(
        max_length=400, default=None, null=True, blank=True
    )  # Unique Addresses
    path = models.URLField(
        max_length=400, default=None, null=True, blank=True
    )  # Relative path to file storage
    md5 = models.CharField(max_length=200, default=None, null=True, blank=True)
    #
    is_deleted = models.BooleanField(default=False)
    created_time = models.DateTimeField()
    updated_time = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = "store_entry"
        ordering = ["-updated_time"]

    def __str__(self):
        return self.title[:30]
