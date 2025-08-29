# audit/apps.py
from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"

    def ready(self):
        # Import signal registrations
        from . import signals  # noqa: F401
        from . import registry  # noqa: F401

        from config.monitoring.metrics import setup_metrics
        setup_metrics()