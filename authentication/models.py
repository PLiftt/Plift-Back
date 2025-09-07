from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

class User(AbstractUser):
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ATHLETE = 'athlete', 'Athlete'
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATHLETE)

    def __str__(self):
        return f"{self.username} ({self.role})"

# Agregar modelo invitation
class Invitation(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations", limit_choices_to={'role': 'coach'})
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_invitations", limit_choices_to={'role': 'athlete'}, null=True, blank=True)
    code = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation from {self.coach.username} to {self.email} - Accepted: {self.accepted}"