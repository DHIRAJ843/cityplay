from django.db import models
from django.conf import settings
from events.models import Event
import secrets


class AddOn(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+₹{self.price})"


class Team(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='captained_teams'
    )
    team_size = models.PositiveIntegerField()
    invite_code = models.CharField(max_length=10, unique=True, editable=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = secrets.token_hex(4)
        super().save(*args, **kwargs)

    @property
    def members_count(self):
        return self.bookings.filter(booking_status='confirmed').count()

    @property
    def open_slots(self):
        return max(0, self.team_size - self.members_count)

    @property
    def is_full(self):
        return self.open_slots <= 0

    def __str__(self):
        return f"{self.name} ({self.members_count}/{self.team_size})"


class Booking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('solo', 'Solo'),
        ('group', 'Group'),
        ('open_slot', 'Open Slot'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    BOOKING_STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')

    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default='solo')
    num_slots = models.PositiveIntegerField(default=1)

    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )

    add_ons = models.ManyToManyField(AddOn, through='BookingAddOn', blank=True)

    entry_fee = models.DecimalField(max_digits=8, decimal_places=2)
    addon_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='confirmed')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.event} ({self.num_slots} slots, {self.booking_type})"


class BookingAddOn(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    addon = models.ForeignKey(AddOn, on_delete=models.PROTECT)
    price_at_booking = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.addon.name} on {self.booking}"