from django.contrib import admin
from .models import Venue, VenueImage, Court


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 3


class CourtInline(admin.TabularInline):
    model = Court
    extra = 1
    fields = ('name', 'is_active', 'base_price', 'peak_price_extra', 'open_hour', 'close_hour')


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'is_active')
    list_filter = ('sector', 'is_active', 'activities')
    search_fields = ('name', 'address', 'sector')
    filter_horizontal = ('activities',)
    inlines = [VenueImageInline, CourtInline]

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'venues/admin_location_picker.js',
        )


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue', 'is_active', 'base_price', 'open_hour', 'close_hour')
    list_filter = ('is_active', 'venue')
    search_fields = ('name', 'venue__name')