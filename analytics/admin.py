from django.contrib import admin
from django.utils import timezone
from .models import AnalyticsCache


@admin.register(AnalyticsCache)
class AnalyticsCacheAdmin(admin.ModelAdmin):
    list_display = ("key", "short_payload", "computed_at", "valid_until", "is_valid_display")
    list_filter = ("computed_at", "valid_until")
    search_fields = ("key",)
    readonly_fields = ("computed_at",)

    def short_payload(self, obj):
        """Show a short preview of the payload JSON."""
        return str(obj.payload)[:75] + "..." if len(str(obj.payload)) > 75 else obj.payload
    short_payload.short_description = "Payload"

    def is_valid_display(self, obj):
        """Custom column to show if cache is still valid."""
        return obj.is_valid()
    is_valid_display.boolean = True  # renders ✓ / ✗
    is_valid_display.short_description = "Is Valid?"