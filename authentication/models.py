from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
import uuid

class User(AbstractUser):
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ATHLETE = 'athlete', 'Athlete'

    class Gender(models.TextChoices):
        MALE = 'male', 'Masculino'
        FEMALE = 'female', 'Femenino'
        OTHER = 'other', 'Otro'

    second_name = models.CharField(max_length=150, blank=True, null=True)
    second_last_name = models.CharField(max_length=150, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATHLETE)

    def __str__(self):
        full_name = f"{self.first_name} {self.second_name or ''} {self.last_name} {self.second_last_name or ''}".strip()
        return f"{self.username} - {full_name} ({self.role}, {self.gender}, {self.date_of_birth})"

# Agregar modelo invitation
class Invitation(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    athlete = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)