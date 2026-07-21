from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('solo/<int:event_id>/', views.solo_booking_confirm, name='solo_booking'),
    path('success/<int:booking_id>/', views.booking_success, name='booking_success'),
]