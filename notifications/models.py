# notifications/models.py
from django.db import models
from django.utils import timezone
from authentication.models import User

# class Notification(models.Model):
#     CHANNEL_CHOICES = [
#         ('SMS', 'SMS'),
#         ('EMAIL', 'Email'),
#         ('WHATSAPP', 'WhatsApp')
#     ]
#     user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
#     channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
#     recipient = models.CharField(max_length=100, help_text="Phone number or email address")
#     message = models.TextField()
#     status = models.CharField(
#         max_length=10,
#         default='pending',
#         choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')]
#     )
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.channel} to {self.user.username if self.user else 'unknown'}: {self.message[:30]}..."

class Notification(models.Model):
    CHANNEL_CHOICES = [('SMS','SMS'), ('EMAIL','Email'), ('WHATSAPP','WhatsApp'), ('INAPP','InApp')]
    STATUS_CHOICES = [
        ('pending','Pending'), ('queued','Queued'), ('sending','Sending'),
        ('sent','Sent'), ('delivered','Delivered'), ('read','Read'), ('failed','Failed')
    ]

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    recipient = models.CharField(max_length=100)  # email/phone/wa
    title = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    category = models.CharField(max_length=32, blank=True)  # e.g. 'payroll', 'system'
    priority = models.SmallIntegerField(default=3)          # 1=high, 5=low

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    provider = models.CharField(max_length=32, blank=True)              # 'twilio', 'whatsapp_cloud', etc.
    provider_message_id = models.CharField(max_length=128, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)               # payloads, error, deeplink, etc.

    scheduled_for = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user','is_read']),
            models.Index(fields=['status']),
            models.Index(fields=['channel','status']),
            models.Index(fields=['timestamp']),             # NEW
            models.Index(fields=['is_read','timestamp']),  # NEW
        ]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['is_read','status','read_at'])

class NotificationPreference(models.Model):
    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp')
    ]
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='notification_preferences')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='EMAIL')
    contact = models.CharField(max_length=100, help_text="Phone number for SMS/WhatsApp or email address for Email")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'channel']
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other preferences for this user
            NotificationPreference.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username if self.user else 'unknown'} prefers {self.channel} at {self.contact}"







