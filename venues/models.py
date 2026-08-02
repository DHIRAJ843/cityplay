from django.db import models
from django.conf import settings
from django.utils import timezone


class Venue(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    sector = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # Which sports/activities this venue offers (Pickleball, Badminton, etc.)
    activities = models.ManyToManyField(
        'events.Activity',
        related_name='venues',
        blank=True,
        help_text="Sports available at this venue."
    )

    # Content for the venue listing + detail pages
    cover_image = models.ImageField(upload_to='venue_images/', blank=True, null=True)
    description = models.TextField(blank=True)

    # Used to calculate "X km away" on the listing page
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # "Things to know" flags shown on the detail page
    duration_label = models.CharField(max_length=50, blank=True, default="1 Hour")
    has_floodlights = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_washroom = models.BooleanField(default=False)
    has_seating_lounge = models.BooleanField(default=False)
    equipment_included = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.sector})"

    class Meta:
        ordering = ['name']


class VenueImage(models.Model):
    """Extra gallery photos for a venue, shown in the 'Gallery' section."""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venue_images/gallery/')
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.venue.name}"