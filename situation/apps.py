from django.apps import AppConfig


class SituationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'situation'

    def ready(self):
        import situation.signals
        # Ensure signals are imported when the app is ready