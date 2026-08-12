from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    path('activity/<slug:slug>/', views.activity_venues, name='activity_venues'),
    path('<int:pk>/', views.venue_detail, name='venue_detail'),
    path('<int:pk>/book/', views.start_booking, name='start_booking'),
    
    # The new checkout route
    path('checkout/', views.checkout, name='checkout'),
    
    path('<int:pk>/favourite/', views.toggle_favourite, name='toggle_favourite'),
    path('review/<int:review_id>/helpful/', views.mark_review_helpful, name='mark_review_helpful'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('resolve-map-link/', views.resolve_map_link, name='resolve_map_link'),
]