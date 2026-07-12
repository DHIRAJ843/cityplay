from django.contrib import admin
from .models import Booking
admin.site.register(Booking)

#TODO TELL THEN TO RUN THE MIGRATION
#TODO TELLL THEM TO INSTALL THE pip install "psycopg[pool]"