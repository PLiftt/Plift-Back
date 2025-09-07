from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ATHLETE = 'athlete', 'Athlete'
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATHLETE)

    def __str__(self):
        return f"{self.username} ({self.role})"



