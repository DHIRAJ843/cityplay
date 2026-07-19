import uuid
from django.db import models
from django.conf import settings
from events.models import Event


class AddOn(models.Model):
    """
    Optional extras a player can attach to a booking (Sports Bib, Water Bottle, etc).
    Kept as its own model (not hardcoded choices) so venue/ops staff can add new
    add-ons from the Django admin without a code change.
    """
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+₹{self.price})"


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

    # related_name='bookings' is REQUIRED — Event.booked_slots depends on it
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')

    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default='solo')
    num_slots = models.PositiveIntegerField(default=1)

    # Groups multiple Booking rows created in one checkout (e.g. a Group booking
    # where one person pays for 5 slots but you still want per-player rows later).
    # Nullable for now — every Solo booking just gets its own random group_id.
    group_id = models.UUIDField(default=uuid.uuid4, editable=False)

    add_ons = models.ManyToManyField(AddOn, through='BookingAddOn', blank=True)

    # --- Price breakdown (snapshotted at booking time, so later price changes
    # to the Event or AddOn never alter a past booking's total) ---
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2)
    addon_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)

    # --- Payment tracking (Razorpay) ---
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
    """
    Through-model for Booking <-> AddOn. Stores price_at_booking so the receipt
    stays accurate even if you change AddOn.price next month.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    addon = models.ForeignKey(AddOn, on_delete=models.PROTECT)
    price_at_booking = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.addon.name} on {self.booking}"