# audit/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet
from . import views

router = DefaultRouter()
router.register(r"audit/logs", AuditLogViewSet, basename="auditlog")

urlpatterns = [path("", include(router.urls))]

urlpatterns += [
    # ... other routes ...
    path("audit/", include("audit.urls_pages")),     # UI pages


]


