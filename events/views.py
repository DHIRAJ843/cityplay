from datetime import date, timedelta
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import Event, Activity
from venues.models import Venue

User = get_user_model()

def homepage(request):
    activity_id = request.GET.get('activity')
    date_filter = request.GET.get('date')
    sector = request.GET.get('sector')
    when = request.GET.get('when', 'all')

    events_qs = Event.objects.filter(status='upcoming').select_related('activity', 'venue')

    if activity_id:
        events_qs = events_qs.filter(activity_id=activity_id)
    if sector:
        events_qs = events_qs.filter(venue__sector=sector)
    if date_filter:
        events_qs = events_qs.filter(date=date_filter)

    today = date.today()
    if when == 'today':
        events_qs = events_qs.filter(date=today)
    elif when == 'tomorrow':
        events_qs = events_qs.filter(date=today + timedelta(days=1))
    elif when == 'weekend':
        saturday = today + timedelta(days=(5 - today.weekday()) % 7)
        events_qs = events_qs.filter(date__in=[saturday, saturday + timedelta(days=1)])

    activities = Activity.objects.filter(is_active=True).annotate(
        event_count=Count('events', filter=Q(events__status='upcoming'))
    )
    sectors = Venue.objects.filter(is_active=True).values_list('sector', flat=True).distinct()

    context = {
        'events': events_qs.order_by('date', 'start_time')[:8],
        'activities': activities,
        'sectors': sectors,
        'total_events': Event.objects.count(),
        'total_venues': Venue.objects.filter(is_active=True).count(),
        'total_players': User.objects.count(),
        'selected_activity': activity_id,
        'selected_date': date_filter,
        'selected_sector': sector,
        'when': when,
    }
    return render(request, 'events/homepage.html', context)