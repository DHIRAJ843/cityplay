from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('solo/<int:event_id>/', views.solo_booking_confirm, name='solo_booking'),
    path('success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]