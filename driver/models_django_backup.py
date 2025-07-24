from django.db import models
from django.utils import timezone

class TrackingStatus(models.Model):
    is_active = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Статус отслеживания'
        verbose_name_plural = 'Статусы отслеживания'

    def __str__(self):
        return f"Отслеживание {'активно' if self.is_active else 'неактивно'}"

class Location(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    distance = models.FloatField(null=True)
    is_at_work = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Координаты: {self.latitude}, {self.longitude} ({self.timestamp})" 