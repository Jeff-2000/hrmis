# monitoring/metrics.py
"""
Custom Prometheus metrics for the HRMIS stack (coexists with django_prometheus).

Because you already use:
    "django_prometheus.middleware.PrometheusBeforeMiddleware"
    "django_prometheus.middleware.PrometheusAfterMiddleware"
we DO NOT export our own HTTP/DB middleware to avoid duplication.

This module adds:
- Celery task lifecycle (received/started/success/failed/retry/revoked, durations)
- Beat last-run timestamp per periodic task
- Auth signals (login/logout/login_failed)
- Exception counts by exception class (complements django_prometheus)
- Integration hooks (Twilio/WhatsApp/Cloudinary)
- Build info + readiness gauge
- Optional sidecar /metrics server (disabled by default if using django_prometheus endpoint)

Wire-up:
    from monitoring.metrics import setup_metrics, mark_beat_run, inc_twilio, inc_whatsapp, inc_cloudinary
    # in apps.py -> AppConfig.ready():
    setup_metrics()

Env:
    METRICS_PORT=9100                     # only used if USE_DJANGO_PROMETHEUS_ENDPOINT != "1"
    USE_DJANGO_PROMETHEUS_ENDPOINT=1      # default; don't start sidecar server
    ENVIRONMENT=development|production
    SERVICE_NAME=hrmis-api
    APP_VERSION=...
    PROMETHEUS_MULTIPROC_DIR=/tmp/metrics # if using gunicorn multiprocess mode
"""

from __future__ import annotations
import os
import time
import socket
from typing import Dict, Optional

from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server

from django.conf import settings
from django.dispatch import receiver
from django.core.signals import got_request_exception
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

# --- Service/environment labels ------------------------------------------------
ENV = getattr(settings, "ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
SERVICE = os.getenv("SERVICE_NAME", "hrmis-api")
HOST = socket.gethostname()
APP_VERSION = os.getenv("APP_VERSION", "dev")

# --- Service meta & health -----------------------------------------------------
BUILD_INFO = Info("hrmis_build_info", "Service build metadata")
BUILD_INFO.info({"service": SERVICE, "env": ENV, "host": HOST, "version": APP_VERSION})

READINESS = Gauge("hrmis_readiness", "Readiness: 1=ready, 0=not ready")
READINESS.set(1)

def set_readiness(ready: bool) -> None:
    READINESS.set(1 if ready else 0)

# --- Exception metrics (complements django_prometheus) -------------------------
HTTP_EXCEPTIONS = Counter(
    "hrmis_http_exceptions_total",
    "Unhandled exceptions by exception class",
    ["exception", "env", "service"],
)

@receiver(got_request_exception)
def _on_exception(sender, request, **kwargs):
    exc = kwargs.get("exception")
    name = exc.__class__.__name__ if exc else "Unknown"
    HTTP_EXCEPTIONS.labels(exception=name, env=ENV, service=SERVICE).inc()

# --- Authentication metrics ----------------------------------------------------
AUTH_LOGINS = Counter(
    "hrmis_auth_logins_total", "Successful user logins", ["method", "env", "service"]
)
AUTH_LOGIN_FAILED = Counter(
    "hrmis_auth_login_failed_total", "Failed login attempts", ["method", "env", "service"]
)
AUTH_LOGOUTS = Counter(
    "hrmis_auth_logouts_total", "User logouts", ["env", "service"]
)

@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):
    m = (request.method or "unknown").upper() if request else "unknown"
    AUTH_LOGINS.labels(method=m, env=ENV, service=SERVICE).inc()

@receiver(user_login_failed)
def _on_login_failed(sender, credentials, request, **kwargs):
    m = (getattr(request, "method", None) or "unknown").upper() if request else "unknown"
    AUTH_LOGIN_FAILED.labels(method=m, env=ENV, service=SERVICE).inc()

@receiver(user_logged_out)
def _on_logout(sender, request, user, **kwargs):
    AUTH_LOGOUTS.labels(env=ENV, service=SERVICE).inc()

# --- Celery metrics ------------------------------------------------------------
START_TIMES: Dict[str, float] = {}

try:
    from celery.signals import (
        task_received, task_prerun, task_postrun, task_failure, task_retry, task_revoked
    )
    CELERY_AVAILABLE = True
except Exception:
    CELERY_AVAILABLE = False

# Buckets tuned for background work
TASK_LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 15, 30, 60, 120, 300, 900)

CELERY_TASK_RECEIVED = Counter(
    "hrmis_celery_task_received_total", "Celery tasks received",
    ["task", "queue", "env", "service"]
)
CELERY_TASK_STARTED = Counter(
    "hrmis_celery_task_started_total", "Celery tasks started",
    ["task", "env", "service"]
)
CELERY_TASK_SUCCEEDED = Counter(
    "hrmis_celery_task_succeeded_total", "Celery tasks succeeded",
    ["task", "env", "service"]
)
CELERY_TASK_FAILED = Counter(
    "hrmis_celery_task_failed_total", "Celery tasks failed",
    ["task", "exc", "env", "service"]
)
CELERY_TASK_RETRIED = Counter(
    "hrmis_celery_task_retried_total", "Celery tasks retried",
    ["task", "env", "service"]
)
CELERY_TASK_REVOKED = Counter(
    "hrmis_celery_task_revoked_total", "Celery tasks revoked",
    ["task", "reason", "env", "service"]
)
CELERY_TASK_DURATION = Histogram(
    "hrmis_celery_task_duration_seconds", "Celery task duration (s)",
    ["task", "env", "service"], buckets=TASK_LATENCY_BUCKETS
)
CELERY_BEAT_LAST_RUN = Gauge(
    "hrmis_celery_beat_task_last_run_timestamp",
    "Epoch timestamp when a periodic task last ran",
    ["task", "env", "service"]
)

def mark_beat_run(task_name: str) -> None:
    """Call inside each periodic (beat) task."""
    CELERY_BEAT_LAST_RUN.labels(task=task_name, env=ENV, service=SERVICE).set(time.time())

def _connect_celery_signals() -> None:
    if not CELERY_AVAILABLE:
        return

    @task_received.connect
    def _received(request=None, **kwargs):
        try:
            task = getattr(request, "name", "unknown")
            queue = getattr(getattr(request, "delivery_info", {}), "get", lambda *_: "default")("routing_key", "default")
        except Exception:
            task, queue = "unknown", "default"
        CELERY_TASK_RECEIVED.labels(task=task, queue=queue, env=ENV, service=SERVICE).inc()

    @task_prerun.connect
    def _prerun(sender=None, task_id=None, task=None, **kwargs):
        START_TIMES[task_id] = time.perf_counter()
        name = sender.name if sender else "unknown"
        CELERY_TASK_STARTED.labels(task=name, env=ENV, service=SERVICE).inc()

    @task_postrun.connect
    def _postrun(sender=None, task_id=None, task=None, **kwargs):
        name = sender.name if sender else "unknown"
        t0 = START_TIMES.pop(task_id, None)
        if t0 is not None:
            CELERY_TASK_DURATION.labels(task=name, env=ENV, service=SERVICE).observe(time.perf_counter() - t0)
        CELERY_TASK_SUCCEEDED.labels(task=name, env=ENV, service=SERVICE).inc()

    @task_failure.connect
    def _failure(sender=None, task_id=None, exception=None, **kwargs):
        name = sender.name if sender else "unknown"
        exc_name = exception.__class__.__name__ if exception else "Unknown"
        CELERY_TASK_FAILED.labels(task=name, exc=exc_name, env=ENV, service=SERVICE).inc()

    @task_retry.connect
    def _retry(sender=None, request=None, **kwargs):
        name = sender.name if sender else "unknown"
        CELERY_TASK_RETRIED.labels(task=name, env=ENV, service=SERVICE).inc()

    @task_revoked.connect
    def _revoked(request=None, terminated=None, signum=None, expired=None, **kwargs):
        name = getattr(request, "task", "unknown")
        reason = "expired" if expired else ("terminated" if terminated else "revoked")
        CELERY_TASK_REVOKED.labels(task=name, reason=reason, env=ENV, service=SERVICE).inc()

# --- Integration hooks ---------------------------------------------------------
TWILIO_WEBHOOKS = Counter(
    "hrmis_twilio_webhooks_total", "Twilio webhooks received",
    ["event", "env", "service"]
)
WHATSAPP_WEBHOOKS = Counter(
    "hrmis_whatsapp_webhooks_total", "WhatsApp webhooks received",
    ["event", "env", "service"]
)
CLOUDINARY_OPS = Counter(
    "hrmis_cloudinary_operations_total", "Cloudinary operations",
    ["op", "env", "service"]
)

def inc_twilio(event: str) -> None:
    TWILIO_WEBHOOKS.labels(event=event, env=ENV, service=SERVICE).inc()

def inc_whatsapp(event: str) -> None:
    WHATSAPP_WEBHOOKS.labels(event=event, env=ENV, service=SERVICE).inc()

def inc_cloudinary(op: str) -> None:
    CLOUDINARY_OPS.labels(op=op, env=ENV, service=SERVICE).inc()

# --- Optional sidecar /metrics server -----------------------------------------
_SERVER_STARTED = False

def start_metrics_http_server_if_needed(default_port: int = 9100) -> Optional[int]:
    """
    Start a separate /metrics HTTP server only if USE_DJANGO_PROMETHEUS_ENDPOINT != "1".
    If you're exposing the Django endpoint (via django_prometheus.urlpatterns), keep the default and do not start this.
    """
    global _SERVER_STARTED
    if os.getenv("USE_DJANGO_PROMETHEUS_ENDPOINT", "1") == "1":
        return None
    if _SERVER_STARTED:
        return int(os.getenv("METRICS_PORT", default_port))

    port = int(os.getenv("METRICS_PORT", default_port))
    start_http_server(port)  # default registry is shared with django_prometheus
    _SERVER_STARTED = True
    return port

# --- Public setup --------------------------------------------------------------
def setup_metrics() -> None:
    """
    Call once from AppConfig.ready().
    - Binds Celery signals (if Celery is installed)
    - Ensures build/readiness gauges are live
    - Optionally starts sidecar /metrics server (when not using django_prometheus endpoint)
    """
    _connect_celery_signals()
    # Only starts a sidecar if explicitly requested
    start_metrics_http_server_if_needed()
