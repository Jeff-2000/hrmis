# integrations/admin.py
from django.contrib import admin
from .models import IntegrationClient


@admin.register(IntegrationClient)
class IntegrationClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "user",
        "is_active",
        "created_at",
    )
    list_filter = ("kind", "is_active", "created_at")
    search_fields = ("name", "user__username", "contact_emails")
    readonly_fields = ("created_at",)
    
    fieldsets = (
        (None, {
            "fields": ("name", "kind", "user", "is_active")
        }),
        ("Security & Permissions", {
            "fields": ("scopes", "ip_allowlist")
        }),
        ("Contacts", {
            "fields": ("contact_emails",)
        }),
        ("Metadata", {
            "fields": ("created_at",),
        }),
    )