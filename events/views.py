from django.shortcuts import render
from .models import Event, Activity

def homepage(request):
    # Fetch only upcoming events, ordered by date to show the closest ones first
    upcoming_events = Event.objects.filter(status='upcoming').order_by('date')[:6]
    
    # Fetch active categories for the filter menu
    activities = Activity.objects.filter(is_active=True)
    
    # Bundle the data into a context dictionary
    context = {
        'events': upcoming_events,
        'activities': activities
    }
    
    # Send the data to the HTML template
    return render(request, 'homepage.html', context)