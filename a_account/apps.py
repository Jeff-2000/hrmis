# a_account/apps.py
from django.apps import AppConfig

class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_account'

    def ready(self):
        from django.db.models.signals import post_save
        from django.conf import settings
        from .models import UserSetting

        def create_settings(sender, instance, created, **kwargs):
            if created:
                UserSetting.objects.get_or_create(user=instance)
        post_save.connect(create_settings, sender=settings.AUTH_USER_MODEL)
        
        from config.monitoring.metrics import setup_metrics
        setup_metrics()



