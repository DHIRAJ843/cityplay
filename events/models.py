from django.db import models
from venues.models import Venue

class Activity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    price_per_slot = models.DecimalField(max_digits=8, decimal_places=2)
    total_slots = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='upcoming')

    def __str__(self):
        return f"{self.title} - {self.date}"