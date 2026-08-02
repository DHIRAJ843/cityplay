from django.contrib import admin
from .models import Venue, VenueImage


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 3


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'is_active')
    list_filter = ('sector', 'is_active', 'activities')
    search_fields = ('name', 'address', 'sector')
    filter_horizontal = ('activities',)
    inlines = [VenueImageInline]

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'venues/admin_location_picker.js',
        )