from django.db import models
import uuid


class StoreTranslate(models.Model):
    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    word = models.CharField(max_length=128)
    info = models.JSONField(default=dict)
    freq = models.IntegerField(default=-1)
    times = models.IntegerField(default=1)
    status = models.CharField(max_length=128, default="not_learned")
    wfrom = models.CharField(max_length=128, default="USER")
    created_time = models.DateTimeField("date created")
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.word

    class Meta:
        db_table = "store_translate"
        ordering = ["created_time"]


class StoreEnglishArticle(models.Model):
    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    title = models.CharField(max_length=128)
    content = models.TextField()
    info = models.JSONField(default=dict)
    created_time = models.DateTimeField("date created")

    def __str__(self):
        return self.title

    class Meta:
        db_table = "store_english_article"
        ordering = ["-created_time"]


class StoreTranslateWord(models.Model):
    idx = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.CharField(max_length=128, null=True, blank=True)
    word = models.CharField(max_length=128)
    regular = models.CharField(max_length=128, null=True, blank=True)
    translation = models.CharField(max_length=128, null=True, blank=True)
    freq = models.IntegerField(default=-1)
    examples = models.JSONField(default=dict)
    created_time = models.DateTimeField("date created")
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.word

    class Meta:
        db_table = "store_translate_word"
        ordering = ["-created_time"]