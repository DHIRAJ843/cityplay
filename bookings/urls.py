from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Yahan views.solo_booking_confirm kar diya taaki views.py se match ho jaye
    path('solo/<int:event_id>/', views.solo_booking_confirm, name='solo_booking'),
]