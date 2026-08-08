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
    @property
    def rating_average(self):
        """Calculates the average rating from all reviews for this venue."""
        all_reviews = self.reviews.all()
        if all_reviews:
            total_score = sum(review.rating for review in all_reviews)
            return round(total_score / len(all_reviews), 1)
        return 4.8  # Default display rating if nobody has reviewed it yet

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


# ==========================================
# NEW MODELS ADDED BELOW (DO NOT DELETE)
# ==========================================

class Court(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='courts')
    name = models.CharField(max_length=100, default="Standard Court")
    is_active = models.BooleanField(default=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=1000.00)
    peak_price_extra = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    open_hour = models.IntegerField(default=6) # 6 AM
    close_hour = models.IntegerField(default=23) # 11 PM

    def is_peak(self, hour):
        # Example: 6 PM to 9 PM is peak pricing
        return 18 <= hour <= 21

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