from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your custom user model with Django's built-in UserAdmin interface
admin.site.register(CustomUser, UserAdmin)