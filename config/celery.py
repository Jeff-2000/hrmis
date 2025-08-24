# hrmis/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
celery_app = Celery('config')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()  # will find tasks.py in each app

from celery.schedules import crontab


celery_app.conf.beat_schedule = {
    'send-leave-reminders': {
        'task': 'leave.tasks.upcoming_leave_reminder',
        'schedule': crontab(hour=8, minute=0),  # Run daily at 8 AM
    },
}