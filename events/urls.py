from django.urls import path
from . import views

app_name = 'events'   # namespace — isse {% url 'events:event_detail' %} likhna padega, clash nahi hoga dusre app ke urls se

urlpatterns = [
    path('<int:pk>/', views.event_detail, name='event_detail'),
]