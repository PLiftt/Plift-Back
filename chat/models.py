from django.db import models

from django.db import models
from authentication.models import User
from training.models import TrainingBlock, TrainingSession

class Conversation(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coach_conversations")
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name="athlete_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("coach", "athlete")

    def __str__(self):
        return f"Conv {self.coach.username} ↔ {self.athlete.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Msg by {self.sender.username} at {self.created_at}"


class Device(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.ANDROID)
    push_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "push_token")

    def __str__(self):
        return f"{self.user.username} - {self.platform}"

