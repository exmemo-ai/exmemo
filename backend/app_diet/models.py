from django.db import models


class StoreDiet(models.Model):
    idx = models.CharField(
        max_length=100, unique=True, primary_key=True, default="default"
    )
    food = models.CharField(max_length=128, null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    kc = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time_of_day = models.CharField(max_length=32, null=True, blank=True)
    uid = models.CharField(max_length=128, default=None)
    created_time = models.DateTimeField("date created", null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True)

    def calc_idx(self):
        # return f"{self.user_name}_{self.food}_{self.date}_{self.time_of_day}"
        return self.calc_idx_static(self.uid, self.food, self.date, self.time_of_day)

    @staticmethod
    def calc_idx_static(uid, food, date, time_of_day):
        return f"{uid}_{food}_{date}_{time_of_day}"

    def save(self, *args, **kwargs):
        self.idx = self.calc_idx()
        super(StoreDiet, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.food[:50]} {self.date} {self.time_of_day}"

    class Meta:
        db_table = "store_diet"
        ordering = ["-created_time"]


class StoreFood(models.Model):
    food = models.CharField(
        max_length=128, unique=True, primary_key=True, default="default"
    )
    kc = models.IntegerField(null=True, blank=True)
    carbs = models.IntegerField(null=True, blank=True)
    fat = models.IntegerField(null=True, blank=True)
    protein = models.IntegerField(null=True, blank=True)
    created_time = models.DateTimeField("date created", null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.food[:50]} {self.kc}"

    class Meta:
        db_table = "store_food"
        ordering = ["-created_time"]
