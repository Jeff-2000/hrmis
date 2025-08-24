# analytics/management/commands/warm_analytics.py
from django.core.management.base import BaseCommand
from analytics.tasks import refresh_analytics_caches

class Command(BaseCommand):
    help = "Precompute analytics caches immediately."
    def handle(self, *args, **opts):
        refresh_analytics_caches.delay()
        self.stdout.write(self.style.SUCCESS("Analytics cache refresh queued."))
