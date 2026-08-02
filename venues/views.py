import re
import urllib.request
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from math import radians, sin, cos, sqrt, atan2

from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from events.models import Activity
from .models import Venue

# Rough centre-point of Gandhinagar, used only to calculate "X km away".
# Swap these for the user's live location later if you add geolocation.
CITY_CENTER_LAT = 23.2156
CITY_CENTER_LNG = 72.6369


def _distance_km(lat, lng):
    """Straight-line (haversine) distance in km from the city center."""
    if lat is None or lng is None:
        return None
    lat1, lng1, lat2, lng2 = map(radians, [CITY_CENTER_LAT, CITY_CENTER_LNG, float(lat), float(lng)])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 6371 * 2 * atan2(sqrt(a), sqrt(1 - a))


def activity_venues(request, slug):
    """
    'Pickleball Courts in <city>' style listing page — every venue
    that offers this activity, shown as cards.
    """
    activity = get_object_or_404(Activity, slug=slug, is_active=True)

    venues = Venue.objects.filter(
        activities=activity,
        is_active=True
    ).prefetch_related('activities').distinct()

    venue_list = []
    for venue in venues:
        venue.distance_km = _distance_km(venue.latitude, venue.longitude)
        venue_list.append(venue)

    under_5 = request.GET.get('under5') == '1'
    if under_5:
        venue_list = [v for v in venue_list if v.distance_km is not None and v.distance_km <= 5]

    venue_list.sort(key=lambda v: (v.distance_km is None, v.distance_km))

    context = {
        'activity': activity,
        'venues': venue_list,
        'total': len(venue_list),
        'under_5': under_5,
    }
    return render(request, 'venues/activity_venues.html', context)


def venue_detail(request, pk):
    """
    Single venue page — gallery, 'Things to know', and a Book Slots CTA
    that jumps into the existing events/booking flow for this venue.
    """
    venue = get_object_or_404(Venue, pk=pk, is_active=True)

    upcoming_events = venue.events.filter(
        status='upcoming',
        date__gte=timezone.localdate()
    ).select_related('activity').order_by('date', 'start_time')[:6]

    context = {
        'venue': venue,
        'gallery': venue.images.all(),
        'venue_activities': venue.activities.filter(is_active=True),
        'upcoming_events': upcoming_events,
        'distance_km': _distance_km(venue.latitude, venue.longitude),
    }
    return render(request, 'venues/venue_detail.html', context)

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