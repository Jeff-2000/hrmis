# config/celery.py
import os
import logging
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

celery_app = Celery('config')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

# ---- PROMETHEUS for Celery ----
try:
    from .monitoring.metrics import _connect_celery_signals, start_metrics_http_server_if_needed
    _connect_celery_signals()
    start_metrics_http_server_if_needed(default_port=int(os.getenv("CELERY_METRICS_PORT", 9100)))
except Exception as e:
    logging.warning("Prometheus for Celery not started: %s", e)

# ---- Beat schedule ----
celery_app.conf.beat_schedule = {
    'daily-attendance-reconciliation': {
        'task': 'attendance.tasks.daily_attendance_reconciliation',
        'schedule': 24*3600,  # every 24 hours
    },
    'check-document-expiry-weekly': {
        'task': 'documents.tasks.check_document_expiry',
        'schedule': 7*24*3600,  # every week
    },
    'check-leaverequest-contract-document-expiry-weekly': {
        'task': 'documents.tasks.check_ContractOrLeaveRequest_document_expiry',
        'schedule': 7*24*3600,  # every week
        # 'schedule': crontab(minute='*/1'),  # alternative: every 1 minute for testing
    },
    'monthly-payroll': {
        'task': 'payroll.tasks.process_monthly_payroll',
        'schedule': 30*24*3600,  # approximate monthly
    },
    'daily-situation-monitor': {
        'task': 'situation.tasks.monitor_situations',
        'schedule': crontab(hour=0, minute=0),  # every day at midnight
    },
    'daily-leave-reminder': {
        'task': 'leave.tasks.upcoming_leave_reminder',
        'schedule': 24*3600,
    },
    'analytics-refresh-5min': {
        'task': 'analytics.tasks.refresh_analytics_caches',
        'schedule': crontab(minute='*/5'),
    },
    'spot-check-cache-integrity': {
        'task': 'analytics.tasks.spot_check_cache_integrity',
        'schedule': crontab(minute=0, hour='*/1'),  # every 1 hour
    },
    'check_contract_expiry': {
        'task': 'documents.tasks.check_contract_expiry',
        'schedule': crontab(day_of_month='1', hour=0, minute=0),  # first day of month at midnight
    },
}