# audit/views_pages.py
from __future__ import annotations
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry

def _can_view_audit(user) -> bool:
    role = (getattr(user, "role", "") or "").upper()
    return user.is_authenticated and (user.is_superuser or role in {"ADMIN", "HR", "AUDITOR"})

@login_required
@user_passes_test(_can_view_audit)
def audit_index_view(request):
    # Build a small, version-tolerant actions list for a filter dropdown
    try:
        actions = [
            {"value": LogEntry.Action.CREATE, "label": "CREATE"},
            {"value": LogEntry.Action.UPDATE, "label": "UPDATE"},
            {"value": LogEntry.Action.DELETE, "label": "DELETE"},
        ]
    except AttributeError:
        # Older django-auditlog versions expose ACTION_* constants instead of .Action enum
        actions = [
            {"value": getattr(LogEntry, "ACTION_CREATE", 0), "label": "CREATE"},
            {"value": getattr(LogEntry, "ACTION_UPDATE", 1), "label": "UPDATE"},
            {"value": getattr(LogEntry, "ACTION_DELETE", 2), "label": "DELETE"},
        ]

    context = {
        "actions": actions,
        "contenttypes": ContentType.objects.all().order_by("app_label", "model"),
    }
    return render(request, "audit/index.html", context)

@login_required
@user_passes_test(_can_view_audit)
def audit_detail_view(request, pk: int):
    entry = get_object_or_404(
        LogEntry.objects.select_related("actor", "content_type"),
        pk=pk,
    )
    # Try to parse JSON changes (django-auditlog stores a JSON string)
    try:
        parsed_changes = json.loads(entry.changes) if entry.changes else None
    except Exception:
        parsed_changes = None

    context = {
        "entry": entry,
        "changes": parsed_changes,  # convenient if your template wants to render a diff table
    }
    return render(request, "audit/detail.html", context)
