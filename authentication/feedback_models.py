# feedback/models.py
from django.db import models
from django.conf import settings

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="feedbacks")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)  # rating can exist w/out comment
    comment = models.TextField(blank=True)                              # optional text
    page_url = models.URLField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, default="open", choices=[("open","Open"),("triaged","Triaged"),("closed","Closed")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback #{self.pk} ({self.rating}) by {self.user or 'anonymous'}"
