from django.utils import timezone


def navbar_booking_count(request):
    """Makes the logged-in user's upcoming booking count available to every
    template automatically — used for the navbar notification badge."""
    if not request.user.is_authenticated:
        return {'navbar_upcoming_count': 0}

    from .models import Booking
    count = Booking.objects.filter(
        user=request.user,
        booking_status='confirmed',
        event__date__gte=timezone.localdate()
    ).count()
    return {'navbar_upcoming_count': count}