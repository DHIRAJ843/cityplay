from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('solo/<int:event_id>/', views.solo_booking_confirm, name='solo_booking'),
    path('team/create/<int:event_id>/', views.create_team, name='create_team'),
    path('team/open-slots/<int:event_id>/', views.open_slots_list, name='open_slots'),
    path('team/join/<int:event_id>/<str:invite_code>/', views.join_team, name='join_team'),
    path('checkout/<int:booking_id>/', views.checkout_view, name='checkout'),
    path('success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('event/<int:event_id>/team/create/', views.create_team, name='create_team'),
path('event/<int:event_id>/open-slots/', views.open_slots_list, name='open_slots'),
path('event/<int:event_id>/join/<str:invite_code>/', views.join_team, name='join_team'),
]