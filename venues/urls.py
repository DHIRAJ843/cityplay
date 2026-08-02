from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    path('activity/<slug:slug>/', views.activity_venues, name='activity_venues'),
    path('resolve-map-link/', views.resolve_map_link, name='resolve_map_link'),
    path('<int:pk>/', views.venue_detail, name='venue_detail'),
]