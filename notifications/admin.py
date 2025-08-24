from django.contrib import admin
from .models import *

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'channel', 'recipient', 'status', 'timestamp', 'is_read', 'delivered_at', 'read_at',
        'title', 'category', 'priority', 'provider', 'provider_message_id', 'retry_count', 'metadata'
    )
    list_filter = ('channel', 'status', 'timestamp')
    search_fields = ('user__username', 'recipient', 'message')
    readonly_fields = ('timestamp',)

    def user_display(self, obj):
        return obj.user.username if obj.user else '—'
    user_display.short_description = 'Utilisateur'

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'channel', 'contact', 'is_active', 'created_at')
    list_filter = ('channel', 'is_active', 'created_at')
    search_fields = ('user__username', 'contact')
    readonly_fields = ('created_at',)

    def user_display(self, obj):
        return obj.user.username if obj.user else '—'
    user_display.short_description = 'Utilisateur'