from django.apps import AppConfig


class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payroll'

    def ready(self):
        from config.monitoring.metrics import setup_metrics
        setup_metrics()