from django.contrib import admin
from .models import Activity, Event


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}  # auto-fills slug as you type name


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity', 'venue', 'date', 'start_time', 'total_slots', 'status')
    list_filter = ('status', 'activity', 'date')
    search_fields = ('title', 'venue__name')
    list_editable = ('status',)  # change status directly from the list view
    date_hierarchy = 'date'
    ordering = ('date', 'start_time')