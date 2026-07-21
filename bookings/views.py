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