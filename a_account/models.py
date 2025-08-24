
# a_account/models.py
from django.db import models
from django.conf import settings

class UserSetting(models.Model):
    THEME_CHOICES = [("system","Système"),("light","Clair"),("dark","Sombre")]
    DATE_FMT_CHOICES = [("YYYY-MM-DD","2025-08-19"),("DD/MM/YYYY","19/08/2025"),("MM/DD/YYYY","08/19/2025")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings")
    locale = models.CharField(max_length=10, default="fr")            # "fr", "en"
    timezone = models.CharField(max_length=64, default="Africa/Abidjan")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="system")
    date_format = models.CharField(max_length=12, choices=DATE_FMT_CHOICES, default="YYYY-MM-DD")
    two_factor_enabled = models.BooleanField(default=False)

    # optional: quiet hours (UI only if you want later)
    quiet_start = models.TimeField(null=True, blank=True)
    quiet_end   = models.TimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user}"



