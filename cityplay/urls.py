"""
URL configuration for cityplay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include  # FIX: Added 'include' here
from django.conf import settings
from django.conf.urls.static import static
from events import views as event_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', event_views.homepage, name='home'),
    
    # FIX: Added the bookings routing. Yeh line Django ko bookings app se jodegi.
    path('bookings/', include('bookings.urls')), 
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)