from django.db import models
from django.conf import settings
from django.utils import timezone


class Venue(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    sector = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    activities = models.ManyToManyField(
        'events.Activity',
        related_name='venues',
        blank=True,
        help_text="Sports available at this venue."
    )

    cover_image = models.ImageField(upload_to='venue_images/', blank=True, null=True)
    description = models.TextField(blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    duration_label = models.CharField(max_length=50, blank=True, default="1 Hour")
    has_floodlights = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_washroom = models.BooleanField(default=False)
    has_seating_lounge = models.BooleanField(default=False)
    equipment_included = models.BooleanField(default=False)
    has_showers = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    live_match_now = models.BooleanField(default=False)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def rating_average(self):
        all_reviews = self.reviews.all()
        if all_reviews:
            total_score = sum(review.rating for review in all_reviews)
            return round(total_score / len(all_reviews), 1)
        return 4.8

    def __str__(self):
        return f"{self.name} ({self.sector})"

    class Meta:
        ordering = ['name']


class VenueImage(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venue_images/gallery/')
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.venue.name}"


class Court(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='courts')
    activity = models.ForeignKey('events.Activity', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, default="Standard Court")
    is_active = models.BooleanField(default=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=1000.00)
    peak_price_extra = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    peak_start_hour = models.IntegerField(default=18)
    peak_end_hour = models.IntegerField(default=21)
    open_hour = models.IntegerField(default=6)
    close_hour = models.IntegerField(default=23)
    order = models.PositiveIntegerField(default=0)

    def is_peak(self, hour):
        return self.peak_start_hour <= hour <= self.peak_end_hour

    def price_for_hour(self, hour):
        if self.is_peak(hour):
            return self.base_price + self.peak_price_extra
        return self.base_price

    def __str__(self):
        return f"{self.venue.name} - {self.name}"


class CourtBooking(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    hour = models.IntegerField()
    status = models.CharField(max_length=20, default='pending')
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    peak_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)


class VenueReview(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    body = models.TextField()

    @property
    def helpful_count(self):
        return self.helpful_votes.count()


class ReviewHelpful(models.Model):
    review = models.ForeignKey(VenueReview, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class VenueFavourite(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='favourites')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)