from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
import uuid

class User(AbstractUser):
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ATHLETE = 'athlete', 'Athlete'
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATHLETE)

    def __str__(self):
        return f"{self.username} ({self.role})"

# Agregar modelo invitation
class Invitation(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    athlete = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)