from django.db import models
from django.conf import settings
from events.models import Event

class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    num_slots = models.PositiveIntegerField(default=1)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    booking_status = models.CharField(max_length=20, default='confirmed')

    def __str__(self):
        return f"{self.user} - {self.event} ({self.num_slots} slots)"