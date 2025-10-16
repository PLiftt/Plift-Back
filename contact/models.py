from django.conf import settings
from django.db import models


class ContactMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="contact_messages"
    )
    email = models.EmailField(blank=True, null=True)  # si no hay user autenticado
    subject = models.CharField(max_length=255)
    message = models.TextField()
    client_request_id = models.CharField(max_length=64, blank=True, default="")
    locale = models.CharField(max_length=16, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.user.email if self.user_id else (self.email or "anon")
        return f"[{self.id}] {who} - {self.subject[:40]}"


def contact_upload_path(instance, filename: str):
    # /media/contact_attachments/2025/10/<message_id>/<filename>
    return f"contact_attachments/{instance.message.created_at:%Y/%m}/{instance.message_id}/{filename}"

def attachment_upload_to(instance, filename):
    # Alias para compatibilidad con migraciones antiguas
    return contact_upload_path(instance, filename)
    
class ContactAttachment(models.Model):
    message = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=contact_upload_path)
    original_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=128, blank=True, default="")
    size = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.message_id} :: {self.original_name or self.file.name}"
