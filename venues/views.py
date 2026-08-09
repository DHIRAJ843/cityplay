import re
import urllib.request
from datetime import timedelta, date as date_cls
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Activity
from .models import Venue, Court, CourtBooking, VenueFavourite, VenueReview, ReviewHelpful

# Rough centre-point of Gandhinagar, used only to calculate "X km away".
CITY_CENTER_LAT = 23.2156
CITY_CENTER_LNG = 72.6369

DAYS_IN_STRIP = 5
ACTIVE_STATUSES = ['pending', 'confirmed', 'blocked']


def _distance_km(lat, lng):
    """Straight-line (haversine) distance in km from the city center."""
    if lat is None or lng is None:
        return None
    lat1, lng1, lat2, lng2 = map(radians, [CITY_CENTER_LAT, CITY_CENTER_LNG, float(lat), float(lng)])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 6371 * 2 * atan2(sqrt(a), sqrt(1 - a))


def _label_for_hour(hour):
    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12
    if display == 0:
        display = 12
    return f"{display}:00 {suffix}"


def _parse_date(raw, fallback):
    if not raw:
        return fallback
    try:
        y, m, d = (int(part) for part in raw.split('-'))
        return date_cls(y, m, d)
    except (ValueError, TypeError):
        return fallback


def activity_venues(request, slug):
    """
    'Pickleball Courts in <city>' style listing page — every venue
    that offers this activity, shown as cards.
    """
    activity = get_object_or_404(Activity, slug=slug, is_active=True)

    venues = Venue.objects.filter(
        activities=activity,
        is_active=True
    ).prefetch_related('activities', 'courts').distinct()

    # --- SEARCH VIA TOP BAR ---
    q = request.GET.get('q', '').strip()
    if q:
        venues = venues.filter(name__icontains=q)

    # --- 1. FILTER BY AMENITIES ---
    amenities = request.GET.getlist('amenity')
    if 'floodlights' in amenities:
        venues = venues.filter(has_floodlights=True)
    if 'parking' in amenities:
        venues = venues.filter(has_parking=True)
    if 'wifi' in amenities:
        venues = venues.filter(has_wifi=True)
    if 'washroom' in amenities:
        venues = venues.filter(has_washroom=True)

    # --- 2. FILTER BY PRICE ---
    price = request.GET.get('price')
    if price == '500':
        venues = venues.filter(courts__base_price__lte=500)
    elif price == '1000':
        venues = venues.filter(courts__base_price__gt=500, courts__base_price__lte=1000)
    elif price == '1000plus':
        venues = venues.filter(courts__base_price__gt=1000)

    # --- 3. DISTANCE & PRICE DISPLAY CALCULATION ---
    venue_list = []
    for venue in venues:
        venue.distance_km = _distance_km(venue.latitude, venue.longitude)
        
        # Grab the lowest court price to display on the card
        court = venue.courts.first()
        venue.display_price = court.base_price if court else Decimal("0.00")
        
        venue_list.append(venue)

    under_5 = request.GET.get('under5') == '1'
    under_10 = request.GET.get('under10') == '1'

    if under_5:
        venue_list = [v for v in venue_list if v.distance_km is not None and v.distance_km <= 5]
    elif under_10:
        venue_list = [v for v in venue_list if v.distance_km is not None and v.distance_km <= 10]

    # --- 4. SORTING VIA TOP BAR ---
    sort_by = request.GET.get('sort', 'Recommended')
    if sort_by == 'Price: Low to High':
        venue_list.sort(key=lambda v: v.display_price)
    elif sort_by == 'Distance':
        venue_list.sort(key=lambda v: (v.distance_km is None, v.distance_km))
    else:
        # Default Recommended: sort by distance
        venue_list.sort(key=lambda v: (v.distance_km is None, v.distance_km))

    context = {
        'activity': activity,
        'venues': venue_list,
        'total': len(venue_list),
        'under_5': under_5,
        'under_10': under_10,
        'amenities': amenities,
        'price': price,
        'q': q,
        'sort': sort_by,
    }
    return render(request, 'venues/activity_venues.html', context)


def _build_slots(court, day, selected_hours):
    """Returns the time-slot grid for one court on one day."""
    if court is None:
        return []

    now = timezone.localtime()
    today = now.date()

    booked = set(
        CourtBooking.objects
        .filter(court=court, date=day, status__in=ACTIVE_STATUSES)
        .values_list('hour', flat=True)
    )

    slots = []
    for hour in range(court.open_hour, court.close_hour):
        past = day < today or (day == today and hour <= now.hour)
        unavailable = past or hour in booked
        slots.append({
            'hour': hour,
            'label': _label_for_hour(hour),
            'available': not unavailable,
            'selected': (not unavailable) and hour in selected_hours,
            'is_peak': court.is_peak(hour),
            'price': court.price_for_hour(hour),
        })
    return slots


def venue_detail(request, pk):
    """
    Full venue page: gallery, amenities, reviews, and the live booking
    panel (date strip -> court -> time slots -> price breakdown).
    """
    venue = get_object_or_404(
        Venue.objects.prefetch_related('images', 'activities', 'courts'),
        pk=pk, is_active=True
    )

    today = timezone.localdate()

    # ---------- date strip ----------
    strip_start = _parse_date(request.GET.get('from'), today)
    if strip_start < today:
        strip_start = today
    selected_date = _parse_date(request.GET.get('date'), strip_start)
    if selected_date < today:
        selected_date = today

    days = []
    for i in range(DAYS_IN_STRIP):
        d = strip_start + timedelta(days=i)
        days.append({
            'date': d,
            'iso': d.isoformat(),
            'is_selected': d == selected_date,
            'is_today': d == today,
        })

    prev_from = strip_start - timedelta(days=DAYS_IN_STRIP)
    has_prev = prev_from >= today
    if not has_prev:
        prev_from = today
    next_from = strip_start + timedelta(days=DAYS_IN_STRIP)

    # ---------- court ----------
    courts = list(venue.courts.filter(is_active=True))
    court = None
    if courts:
        raw_court = request.GET.get('court')
        if raw_court and raw_court.isdigit():
            court = next((c for c in courts if c.id == int(raw_court)), None)
        court = court or courts[0]

    # ---------- slots ----------
    selected_hours = set()
    for raw in request.GET.getlist('slot'):
        if raw.isdigit():
            selected_hours.add(int(raw))

    slots = _build_slots(court, selected_date, selected_hours)
    chosen = [s for s in slots if s['selected']]

    base_total = sum((court.base_price for _ in chosen), Decimal("0.00")) if court else Decimal("0.00")
    peak_total = sum(
        (court.peak_price_extra for s in chosen if s['is_peak']), Decimal("0.00")
    ) if court else Decimal("0.00")
    platform_fee = venue.platform_fee if chosen else Decimal("0.00")
    total_price = base_total + peak_total + platform_fee

    # ---------- reviews ----------
    reviews = (VenueReview.objects
               .filter(venue=venue)
               .select_related('user')
               .prefetch_related('helpful_votes'))

    is_favourite = False
    if request.user.is_authenticated:
        is_favourite = VenueFavourite.objects.filter(venue=venue, user=request.user).exists()

    gallery = list(venue.images.all())

    upcoming_events = venue.events.filter(
        status='upcoming',
        date__gte=today
    ).select_related('activity').order_by('date', 'start_time')[:6]

    context = {
        'venue': venue,
        'gallery': gallery,
        'gallery_thumbs': gallery[:5],
        'extra_photo_count': max(len(gallery) - 5, 0),
        'venue_activities': venue.activities.filter(is_active=True),
        'upcoming_events': upcoming_events,
        'distance_km': _distance_km(venue.latitude, venue.longitude),

        'days': days,
        'selected_date': selected_date,
        'strip_from': strip_start.isoformat(),
        'prev_from': prev_from.isoformat(),
        'next_from': next_from.isoformat(),
        'has_prev': has_prev,

        'courts': courts,
        'active_court': court,
        'slots': slots,
        'selected_slots': chosen,
        'selected_hours_csv': ",".join(str(s['hour']) for s in chosen),

        'base_total': base_total,
        'peak_total': peak_total,
        'platform_fee': platform_fee,
        'total_price': total_price,

        'reviews': reviews,
        'review_count': len(reviews),
        'rating_average': venue.rating_average,
        'is_favourite': is_favourite,
    }
    return render(request, 'venues/venue_detail.html', context)


@login_required
@require_POST
def start_booking(request, pk):
    """Creates pending CourtBookings for the selected slots, then sends the user to payment."""
    venue = get_object_or_404(Venue, pk=pk, is_active=True)
    court = get_object_or_404(Court, pk=request.POST.get('court'), venue=venue, is_active=True)
    day = _parse_date(request.POST.get('date'), timezone.localdate())

    hours = sorted({int(h) for h in request.POST.get('slots', '').split(',') if h.strip().isdigit()})
    if not hours:
        messages.error(request, "Please pick at least one time slot.")
        return redirect(f"{reverse('venues:venue_detail', args=[venue.pk])}?date={day.isoformat()}&court={court.pk}")

    created = []
    try:
        with transaction.atomic():
            for hour in hours:
                base = court.base_price
                peak = court.peak_price_extra if court.is_peak(hour) else Decimal("0.00")
                fee = venue.platform_fee if hour == hours[0] else Decimal("0.00")
                created.append(CourtBooking.objects.create(
                    court=court, user=request.user, date=day, hour=hour, status='pending',
                    base_price=base, peak_charge=peak, platform_fee=fee,
                    total_price=base + peak + fee,
                ))
    except IntegrityError:
        messages.error(request, "Sorry, one of those slots was just taken. Please pick another.")
        return redirect(f"{reverse('venues:venue_detail', args=[venue.pk])}?date={day.isoformat()}&court={court.pk}")

    request.session['pending_court_bookings'] = [b.pk for b in created]

    # Hook into your existing payment flow if it exists; otherwise land on My Bookings.
    for name in ('bookings:payment', 'bookings:checkout', 'bookings:my_bookings'):
        try:
            return redirect(reverse(name))
        except NoReverseMatch:
            continue
    return redirect('venues:venue_detail', pk=venue.pk)


@login_required
@require_POST
def toggle_favourite(request, pk):
    venue = get_object_or_404(Venue, pk=pk, is_active=True)
    fav, created = VenueFavourite.objects.get_or_create(venue=venue, user=request.user)
    if not created:
        fav.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'favourited': created})
    return redirect(request.META.get('HTTP_REFERER') or reverse('venues:venue_detail', args=[venue.pk]))


@login_required
@require_POST
def mark_review_helpful(request, review_id):
    review = get_object_or_404(VenueReview, pk=review_id)
    vote, created = ReviewHelpful.objects.get_or_create(review=review, user=request.user)
    if not created:
        vote.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'helpful': created, 'count': review.helpful_count})
    return redirect(request.META.get('HTTP_REFERER') or reverse('venues:venue_detail', args=[review.venue_id]))


@login_required
@require_POST
def add_review(request, pk):
    venue = get_object_or_404(Venue, pk=pk, is_active=True)
    body = (request.POST.get('body') or '').strip()
    try:
        rating = max(1, min(5, int(request.POST.get('rating', 5))))
    except (TypeError, ValueError):
        rating = 5

    if not body:
        messages.error(request, "Please write something before posting your review.")
    else:
        VenueReview.objects.update_or_create(
            venue=venue, user=request.user,
            defaults={'rating': rating, 'body': body},
        )
        messages.success(request, "Thanks for the review!")
    return redirect('venues:venue_detail', pk=venue.pk)


@staff_member_required
def resolve_map_link(request):
    """
    Admin helper: given any Google Maps link (including short
    maps.app.goo.gl links), follow redirects and pull out lat/lng.
    """
    url = request.GET.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'No URL provided'}, status=400)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        final_url = resp.geturl()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    patterns = [
        r'@(-?\d+\.\d+),(-?\d+\.\d+)',
        r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',
        r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, final_url)
        if m:
            return JsonResponse({'lat': m.group(1), 'lng': m.group(2)})

    return JsonResponse({'error': 'Could not find coordinates in that link'}, status=404)