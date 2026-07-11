from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Extends Django's base user to include role-based logic for the FieldDay platform.
    """
    class Role(models.TextChoices):
        PLAYER = 'PLAYER', 'Player'
        VENUE_OWNER = 'VENUE_OWNER', 'Venue Owner'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PLAYER
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"