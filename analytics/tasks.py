# analytics/tasks.py
from celery import shared_task
from django.utils import timezone
from .cache import *
from .services import *
from config.monitoring.metrics import mark_beat_run

TTL_SHORT = 5 * 60     # 5 min
TTL_MED   = 15 * 60    # 15 min
TTL_LONG  = 60 * 60    # 1 hour

@shared_task
def refresh_analytics_caches():
    
    # Mark task as run in monitoring
    mark_beat_run("analytics.tasks.refresh_analytics_caches")
    
    # compute and cache; failures in one block don’t stop others
    try: set_cache("analytics:kpis", compute_kpis(), TTL_SHORT)
    except Exception: pass
    try: set_cache("analytics:headcount", compute_headcount_series(), TTL_LONG)
    except Exception: pass
    try: set_cache("analytics:leave_series", compute_leave_series(), TTL_LONG)
    except Exception: pass
    try: set_cache("analytics:leave_sla", compute_leave_sla(), TTL_MED)
    except Exception: pass
    try: set_cache("analytics:payroll_components", compute_payroll_components(), TTL_MED)
    except Exception: pass
    try: set_cache("analytics:attrition_top", compute_attrition_top(), TTL_MED)
    except Exception: pass


@shared_task
def spot_check_cache_integrity():
    
    # Mark task as run in monitoring
    mark_beat_run("analytics.tasks.spot_check_cache_integrity")
    
    # recompute KPIs and compare to cached
    key = "analytics:kpis"
    cached, _ = get_or_set_with_source(key, compute_kpis, 300)
    fresh = compute_kpis()
    if cached != fresh:
        # log / send alert; here we just refresh to self-heal
        set_with_source(key, fresh, 300)
