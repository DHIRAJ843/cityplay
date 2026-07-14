from django.db import models
from django.conf import settings
from django.utils.text import slugify
from venues.models import Venue


class Activity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon_image = models.ImageField(upload_to='activity_icons/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Activities"


class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name='events')
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name='events')
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price_per_slot = models.DecimalField(max_digits=8, decimal_places=2)
    total_slots = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"

    @property
    def booked_slots(self):
        """Sum of confirmed booking slots for this event. Computed live, not stored,
        so it can never drift out of sync with actual bookings."""
        from bookings.models import Booking
        result = self.bookings.filter(
            booking_status='confirmed'
        ).aggregate(total=models.Sum('num_slots'))
        return result['total'] or 0

    @property
    def spots_left(self):
        return self.total_slots - self.booked_slots

    @property
    def urgency_label(self):
        if self.spots_left <= 0:
            return "Sold Out"
        ratio = self.spots_left / self.total_slots if self.total_slots else 0
        if ratio <= 0.3:
            return "Filling fast"
        return f"{self.spots_left} spots left"

    @property
    def spots_left_percent(self):
        if not self.total_slots:
            return 0
        return max(0, min(100, round((self.spots_left / self.total_slots) * 100)))

    class Meta:
        ordering = ['date', 'start_time']