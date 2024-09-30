from django.db import models


class StoreUser(models.Model):
    user_id = models.CharField(
        max_length=128, unique=True, primary_key=True, default="default"
    )
    alias = models.CharField(max_length=512, null=True, blank=True)
    settings = models.CharField(max_length=4096, null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    created_time = models.DateTimeField("date created", null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id}"

    class Meta:
        db_table = "store_user_settings"
        ordering = ["-created_time"]


class StoreResourceUsage(models.Model):
    user_id = models.CharField(max_length=128, null=True, blank=True)
    app = models.CharField(max_length=128, null=True, blank=True)
    rtype = models.CharField(max_length=128, null=True, blank=True)  # tts/llm
    amount = models.IntegerField()
    status = models.CharField(max_length=64, default="success")
    during = models.FloatField(default=0.0)
    method = models.CharField(max_length=32, null=True, blank=True)
    info = models.CharField(max_length=1024, null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} {self.rtype} {self.amount} {self.status}"

    class Meta:
        db_table = "store_resource_usage"
        ordering = ["-updated_time"]
