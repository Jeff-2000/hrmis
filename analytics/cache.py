# analytics/cache.py
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import AnalyticsCache

# ################################################################################
# # - L1: In-memory/Redis cache -> fastet
# # - L2: DB fallback cache (our AnalyticsCache table) -> still fast, survives Redis outages/restarts
# # - L3: Direct computation (your original, “fit=rst method”) -> source of thruth and fallback when caches miss or are stale.
# # Cache management to choose between L1, L2, or L3:
# def get_with_source(key: str):
#     data = cache.get(key)
#     if data is not None:
#         return data, "L1"
#     row = AnalyticsCache.objects.filter(key=key).first()
#     if row and row.valid_until and row.valid_until > timezone.now():
#         # warm L1 for the remaining TTL
#         ttl = int((row.valid_until - timezone.now()).total_seconds())
#         if ttl > 0:
#             cache.set(key, row.payload, ttl)
#         return row.payload, "L2"
#     return None, None

# def set_with_source(key: str, data: dict, ttl_seconds: int = 900):
#     cache.set(key, data, ttl_seconds)  # L1
#     valid_until = timezone.now() + timedelta(seconds=ttl_seconds)
#     AnalyticsCache.objects.update_or_create(
#         key=key, defaults={'payload': data, 'valid_until': valid_until}
#     )
#     return data, "L1+L2"

# def get_or_set_with_source(key: str, producer, ttl_seconds: int = 900):
#     data, src = get_with_source(key)
#     if data is not None:
#         return data, src
#     # compute (L3) then populate caches
#     data = producer()
#     _, _ = set_with_source(key, data, ttl_seconds)
#     return data, "compute→cached"

# ################################################################################

# ############################################################################
# # For For Working with Django's cache framework 
# def set_cache(key: str, data: dict, ttl_seconds: int = 900):
#     # Redis/LocMem
#     cache.set(key, data, ttl_seconds)
#     # DB fallback
#     valid_until = timezone.now() + timedelta(seconds=ttl_seconds)
#     AnalyticsCache.objects.update_or_create(
#         key=key, defaults={'payload': data, 'valid_until': valid_until}
#     )
#     return data

# def get_cache(key: str):
#     data = cache.get(key)
#     if data is not None:
#         return data
#     # DB fallback
#     row = AnalyticsCache.objects.filter(key=key).first()
#     if row and row.is_valid():
#         # warm the in-memory/redis cache for next call
#         ttl = int((row.valid_until - timezone.now()).total_seconds())
#         if ttl > 0:
#             cache.set(key, row.payload, ttl)
#         return row.payload
#     return None

# def get_or_set(key: str, producer, ttl_seconds: int = 900):
#     data = get_cache(key)
#     if data is not None:
#         return data
#     data = producer()
#     return set_cache(key, data, ttl_seconds)

# ############################################################################



# analytics/cache.py
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from .models import AnalyticsCache  # key: str, payload: JSON, valid_until: DateTime

def get_or_set(key: str, producer, ttl_seconds: int = 900):
    """Simple L1+L2 cache (no source tag)."""
    val = cache.get(key)
    if val is not None:
        return val
    row = AnalyticsCache.objects.filter(key=key).first()
    if row and row.valid_until and row.valid_until > timezone.now():
        ttl = int((row.valid_until - timezone.now()).total_seconds())
        if ttl > 0:
            cache.set(key, row.payload, ttl)
        return row.payload
    data = producer()
    set_cache(key, data, ttl_seconds)
    return data

def set_cache(key: str, data, ttl_seconds: int = 900):
    cache.set(key, data, ttl_seconds)  # L1
    AnalyticsCache.objects.update_or_create(
        key=key,
        defaults={"payload": data, "valid_until": timezone.now() + timedelta(seconds=ttl_seconds)}
    )
    return data

# Instrumented versions (with source tags)

def get_with_source(key: str):
    val = cache.get(key)
    if val is not None:
        return val, "L1"
    row = AnalyticsCache.objects.filter(key=key).first()
    if row and row.valid_until and row.valid_until > timezone.now():
        ttl = int((row.valid_until - timezone.now()).total_seconds())
        if ttl > 0:
            cache.set(key, row.payload, ttl)
        return row.payload, "L2"
    return None, None

def set_with_source(key: str, data, ttl_seconds: int = 900):
    set_cache(key, data, ttl_seconds)
    return data, "L1+L2"

def get_or_set_with_source(key: str, producer, ttl_seconds: int = 900):
    data, src = get_with_source(key)
    if data is not None:
        return data, src
    data = producer()
    set_with_source(key, data, ttl_seconds)
    return data, "compute→cached"











