from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ContactMessage, ContactAttachment


class ContactAttachmentInline(admin.TabularInline):
    model = ContactAttachment
    extra = 0


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "subject", "created_at")
    search_fields = ("email", "subject", "message", "client_request_id")
    list_filter = ("created_at",)
    inlines = [ContactAttachmentInline]


@admin.register(ContactAttachment)
class ContactAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "original_name", "size")
    search_fields = ("original_name",)
