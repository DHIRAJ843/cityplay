"""
URL configuration for cityplay project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from events import views as event_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', event_views.homepage, name='home'),
    path('about/', event_views.about_us, name='about'),

    path('events/', include('events.urls')),
    path('bookings/', include('bookings.urls')),
    path('accounts/', include('accounts.urls')),

    # Venue directory + venue detail pages (Pickleball courts listing, etc.)
    path('venues/', include('venues.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)