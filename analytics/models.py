# analytics/models.py
from django.db import models
from django.utils import timezone

class AnalyticsCache(models.Model):
    key = models.CharField(max_length=100, unique=True, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    computed_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['valid_until'])]
        ordering = ['-computed_at']

    def is_valid(self):
        return self.valid_until and self.valid_until > timezone.now()








