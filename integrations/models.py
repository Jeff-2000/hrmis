# integrations/models.py
from django.db import models

class IntegrationClient(models.Model):
    KIND_CHOICES = [("BANK","Bank"),("PAYROLL_ENGINE","External Payroll"),("BIOMETRIC_GATEWAY","Biometric")]
    name = models.CharField(max_length=100, unique=True)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    user = models.OneToOneField("authentication.User", on_delete=models.PROTECT)  # JWT user that represents this client
    scopes = models.JSONField(default=list, blank=True)  # ["payroll.upload","attendance.punch"]
    ip_allowlist = models.JSONField(default=list, blank=True)  # ["102.64.0.0/12", ...]
    is_active = models.BooleanField(default=True)
    contact_emails = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

