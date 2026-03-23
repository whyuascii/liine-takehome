from django.db import models

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Restaurant(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class OpeningHours(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="opening_hours"
    )
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        indexes = [
            models.Index(fields=["day_of_week", "open_time", "close_time"]),
        ]

    def __str__(self):
        day = DAY_NAMES[self.day_of_week]
        return f"{self.restaurant.name} - {day} {self.open_time.strftime('%H:%M')}-{self.close_time.strftime('%H:%M')}"
