from django.db import models

from django.db import models
from authentication.models import CustomUser
from training.models import TrainingBlock, TrainingSession

class Conversation(models.Model):
    coach = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="coach_conversations")
    athlete = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="athlete_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("coach", "athlete")


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)



class Device(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"
        OTHER = "OTHER", "Other"

    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.ANDROID)
    push_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)



