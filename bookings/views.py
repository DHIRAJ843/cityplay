from django.shortcuts import render

# Create your views here.
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from events.models import Event
from .models import Booking, BookingAddOn, AddOn

PLATFORM_FEE = Decimal('5.00')  # flat fee for now, mockup mein bhi yahi hai


@login_required  # bina login ke booking page pe koi na pahuche
def solo_booking_confirm(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    addons = AddOn.objects.filter(is_active=True)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('addons')
        selected_addons = AddOn.objects.filter(id__in=selected_ids, is_active=True)

        with transaction.atomic():
            # select_for_update() = row LOCK. Jab tak yeh transaction khatam
            # nahi hota, koi doosra request isi event ko simultaneously book
            # nahi kar sakta. Isse "2 log ek saath last spot book kar lein"
            # wala race condition nahi hoga.
            locked_event = Event.objects.select_for_update().get(pk=event.pk)

            if locked_event.spots_left < 1:
                messages.error(request, "Sorry bro, event sold out ho gaya.")
                return redirect('events:event_detail', pk=event.pk)

            addon_total = sum((a.price for a in selected_addons), Decimal('0'))
            entry_fee = locked_event.price_per_slot
            total_amount = entry_fee + addon_total + PLATFORM_FEE

            booking = Booking.objects.create(
                event=locked_event,
                user=request.user,
                booking_type='solo',
                num_slots=1,
                entry_fee=entry_fee,
                addon_total=addon_total,
                platform_fee=PLATFORM_FEE,
                total_amount=total_amount,
                payment_status='pending',   # Razorpay abhi wire nahi hua, isliye pending
                booking_status='confirmed',
            )

            for addon in selected_addons:
                BookingAddOn.objects.create(
                    booking=booking, addon=addon, price_at_booking=addon.price
                )

        # TODO: yahan Razorpay order create karke payment page pe redirect karenge
        return redirect('bookings:booking_success', booking_id=booking.id)

    return render(request, 'bookings/solo_confirm.html', {
        'event': event, 
        'addons': addons, 
        'platform_fee': PLATFORM_FEE,
        'initial_total': event.price_per_slot + PLATFORM_FEE,
    })


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'bookings/booking_success.html', {'booking': booking})
from django.utils import timezone
from django.contrib import messages as dj_messages

ACTIVITY_THEMES = {
    'football': '#173a2e',
    'badminton': '#16324f',
    'basketball': '#3f3f3f',
    'cricket': '#2c4a1e',
    'tennis': '#1f4d3d',
}
FALLBACK_THEMES = ['#173a2e', '#16324f', '#3f3f3f', '#4a2c1e', '#2e2e50']


def _theme_for(activity_name):
    key = (activity_name or '').strip().lower()
    if key in ACTIVITY_THEMES:
        return ACTIVITY_THEMES[key]
    return FALLBACK_THEMES[hash(key) % len(FALLBACK_THEMES)]


@login_required
def my_bookings_view(request):
    today = timezone.localdate()

    bookings_qs = (
        Booking.objects
        .filter(user=request.user)
        .select_related('event', 'event__activity', 'event__venue')
        .order_by('-event__date', '-event__start_time')
    )

    upcoming, past, cancelled = [], [], []

    for b in bookings_qs:
        b.theme_color = _theme_for(b.event.activity.name)
        b.ticket_code = f"CPY{b.id:06d}"

        if b.booking_status == 'cancelled':
            cancelled.append(b)
        elif b.event.date >= today:
            upcoming.append(b)
        else:
            past.append(b)

    paid_total = sum(
        (b.total_amount for b in bookings_qs if b.payment_status == 'paid'),
        Decimal('0')
    )

    context = {
        'upcoming': upcoming,
        'past': past,
        'cancelled': cancelled,
        'upcoming_count': len(upcoming),
        'played_count': len(past),
        'total_spent': paid_total,
    }
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    if request.method == 'POST':
        if booking.booking_status == 'confirmed' and booking.event.date >= timezone.localdate():
            booking.booking_status = 'cancelled'
            booking.save(update_fields=['booking_status'])
            dj_messages.success(request, 'Booking cancelled.')
        else:
            dj_messages.error(request, "This booking can't be cancelled.")

    return redirect('bookings:my_bookings')