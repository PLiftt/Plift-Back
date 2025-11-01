from django.db import models
from authentication.models import CustomUser

class PushToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notification_tokens")
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)