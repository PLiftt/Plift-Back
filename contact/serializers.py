from rest_framework import serializers
from .models import ContactMessage, ContactAttachment


class ContactAttachmentOut(serializers.ModelSerializer):
    class Meta:
        model = ContactAttachment
        fields = ["id", "original_name", "content_type", "size", "file"]


class ContactMessageOut(serializers.ModelSerializer):
    attachments = ContactAttachmentOut(many=True, read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            "id", "email", "subject", "message", "client_request_id",
            "locale", "created_at", "attachments"
        ]
