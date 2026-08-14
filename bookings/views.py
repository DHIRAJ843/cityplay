import secrets
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib import messages as dj_messages
from events.models import Event
from .models import Booking, BookingAddOn, AddOn, Team

PLATFORM_FEE = Decimal('5.00')

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
def solo_booking_confirm(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    addons = AddOn.objects.filter(is_active=True)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('addons')
        selected_addons = AddOn.objects.filter(id__in=selected_ids, is_active=True)

        with transaction.atomic():
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
                payment_status='pending',
                booking_status='confirmed',
            )

            for addon in selected_addons:
                BookingAddOn.objects.create(
                    booking=booking, addon=addon, price_at_booking=addon.price
                )

        return redirect('bookings:checkout', booking_id=booking.id)

    return render(request, 'bookings/solo_confirm.html', {
        'event': event,
        'addons': addons,
        'platform_fee': PLATFORM_FEE,
        'initial_total': event.price_per_slot + PLATFORM_FEE,
    })


@login_required
def create_team(request, event_id):
    """Step 1 of group booking: captain names the team and sets its size."""
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        name = (request.POST.get('team_name') or '').strip()
        try:
            team_size = int(request.POST.get('team_size', 0))
        except (TypeError, ValueError):
            team_size = 0

        if not name:
            messages.error(request, "Please give your team a name.")
            return render(request, 'bookings/create_team.html', {'event': event})

        if team_size < 2 or team_size > 50:
            messages.error(request, "Team size must be between 2 and 50.")
            return render(request, 'bookings/create_team.html', {'event': event})

        with transaction.atomic():
            locked_event = Event.objects.select_for_update().get(pk=event.pk)

            if locked_event.spots_left < 1:
                messages.error(request, "Sorry, this event is sold out.")
                return redirect('events:event_detail', pk=event.pk)

            team = Team.objects.create(
                event=locked_event,
                name=name,
                captain=request.user,
                team_size=team_size,
            )

            entry_fee = locked_event.price_per_slot
            total_amount = entry_fee + PLATFORM_FEE

            booking = Booking.objects.create(
                event=locked_event,
                user=request.user,
                booking_type='group',
                num_slots=1,
                team=team,
                entry_fee=entry_fee,
                platform_fee=PLATFORM_FEE,
                total_amount=total_amount,
                payment_status='pending',
                booking_status='confirmed',
            )

        messages.success(
            request,
            f"Team '{team.name}' created! Share this code with your squad: {team.invite_code}"
        )
        return redirect('bookings:checkout', booking_id=booking.id)

    return render(request, 'bookings/create_team.html', {'event': event})


@login_required
def open_slots_list(request, event_id):
    """Browse all teams for this event that still need players."""
    event = get_object_or_404(Event, pk=event_id)

    all_teams = Team.objects.filter(event=event).select_related('captain')
    already_joined_ids = set(
        Booking.objects.filter(
            event=event, user=request.user, booking_status='confirmed', team__isnull=False
        ).values_list('team_id', flat=True)
    )

    open_teams = [
        t for t in all_teams
        if not t.is_full and t.id not in already_joined_ids
    ]

    return render(request, 'bookings/open_slots.html', {
        'event': event,
        'open_teams': open_teams,
    })


@login_required
def join_team(request, event_id, invite_code):
    """Step where a solo player joins an existing team via its invite code."""
    event = get_object_or_404(Event, pk=event_id)
    team = get_object_or_404(Team, event=event, invite_code=invite_code)

    already_in = Booking.objects.filter(
        event=event, user=request.user, team=team, booking_status='confirmed'
    ).exists()

    if request.method == 'POST':
        if already_in:
            messages.info(request, "You're already part of this team.")
            return redirect('bookings:my_bookings')

        with transaction.atomic():
            locked_event = Event.objects.select_for_update().get(pk=event.pk)
            locked_team = Team.objects.select_for_update().get(pk=team.pk)

            if locked_event.spots_left < 1:
                messages.error(request, "Sorry, this event is sold out.")
                return redirect('events:event_detail', pk=event.pk)

            if locked_team.is_full:
                messages.error(request, "This team just filled up. Try another one.")
                return redirect('bookings:open_slots', event_id=event.id)

            entry_fee = locked_event.price_per_slot
            total_amount = entry_fee + PLATFORM_FEE

            booking = Booking.objects.create(
                event=locked_event,
                user=request.user,
                booking_type='open_slot',
                num_slots=1,
                team=locked_team,
                entry_fee=entry_fee,
                platform_fee=PLATFORM_FEE,
                total_amount=total_amount,
                payment_status='pending',
                booking_status='confirmed',
            )

        messages.success(request, f"You joined '{team.name}'! Complete payment to confirm your spot.")
        return redirect('bookings:checkout', booking_id=booking.id)

    return render(request, 'bookings/join_team.html', {
        'event': event,
        'team': team,
        'already_in': already_in,
    })


@login_required
def checkout_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    venue = booking.event.venue
    base_total = booking.entry_fee
    platform_fee = booking.platform_fee
    convenience_fee = round(float(base_total) * 0.02, 2)
    total_price = base_total + platform_fee + Decimal(str(convenience_fee))

    return render(request, 'bookings/checkout.html', {
        'booking': booking,
        'venue': venue,
        'bookings': [booking],
        'first_booking': booking,
        'base_total': base_total,
        'platform_fee': platform_fee,
        'convenience_fee': convenience_fee,
        'total_price': total_price,
    })


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'bookings/booking_success.html', {'booking': booking})


@login_required
def my_bookings_view(request):
    today = timezone.localdate()

    bookings_qs = (
        Booking.objects
        .filter(user=request.user)
        .select_related('event', 'event__activity', 'event__venue', 'team')
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