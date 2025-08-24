# analytics/views.py
from __future__ import annotations
from datetime import date, timedelta
from calendar import monthrange
from collections import defaultdict

from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from employee.models import Employee
from leave.models import LeaveRequest
from payroll.models import Payslip, PayrollRun, PayslipItem, Contract
from notifications.models import Notification

from .cache import get_or_set_with_source, set_with_source
from .services import (
    compute_kpis,
    compute_headcount_series,
    compute_leave_series,
    compute_leave_sla,
    compute_payroll_components,
    compute_attrition_top,
)

# ---------- small helpers ----------

def _add_month(d: date, k: int = 1) -> date:
    y = d.year + (d.month + k - 1) // 12
    m = (d.month + k - 1) % 12 + 1
    last = monthrange(y, m)[1]
    return date(y, m, min(d.day, last))

# ---------- template ----------

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "analytics/dashboard.html"

# ---------- cache orchestration ----------

def _maybe_fresh(request, key, fn, ttl_seconds: int):
    fresh = request.query_params.get("fresh", "").lower() in ("1", "true", "yes")
    if fresh:
        data = fn()  # L3 compute
        set_with_source(key, data, ttl_seconds)
        return data, "fresh-compute"
    return get_or_set_with_source(key, fn, ttl_seconds)

# ---------- APIs ----------

class KPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:kpis", compute_kpis, 300)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class HeadcountForecastView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:headcount", compute_headcount_series, 3600)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class LeaveForecastView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:leave_series", compute_leave_series, 3600)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class LeaveSLAView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:leave_sla", compute_leave_sla, 900)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class PayrollComponentsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:payroll_components", compute_payroll_components, 900)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class AttritionRiskView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data, src = _maybe_fresh(request, "analytics:attrition_top", compute_attrition_top, 900)
        resp = Response(data); resp["X-Analytics-Source"] = src; return resp

class NotificationEngagementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        since = timezone.now() - timedelta(days=90)
        qs = Notification.objects.filter(timestamp__gte=since)

        by_channel = (
            qs.values("channel")
              .annotate(
                  sent=Count("id"),
                  read=Count("id", filter=Q(is_read=True)),
              )
              .order_by("channel")
        )

        unread_dist = (
            Notification.objects.filter(is_read=False)
            .values("user__role")
            .annotate(n=Count("id"))
            .order_by()
        )

        data = {
            "channels": [
                {
                    "channel": r["channel"],
                    "sent": r["sent"],
                    "read": int(r["read"] or 0),
                    "read_rate": round((int(r["read"] or 0) / r["sent"] * 100.0), 1) if r["sent"] else 0.0,
                }
                for r in by_channel
            ],
            "unread_by_role": [
                {"role": x["user__role"] or "UNKNOWN", "count": x["n"]} for x in unread_dist
            ],
        }
        resp = Response(data)
        resp["X-Analytics-Source"] = "compute"  # this one is quick; you can cache if you want
        return resp

class SummaryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        kpis, src_k = _maybe_fresh(request, "analytics:kpis", compute_kpis, 300)
        hc,   src_h = _maybe_fresh(request, "analytics:headcount", compute_headcount_series, 3600)
        ls,  src_ls = _maybe_fresh(request, "analytics:leave_series", compute_leave_series, 3600)
        sla, src_s  = _maybe_fresh(request, "analytics:leave_sla", compute_leave_sla, 900)
        pc,  src_p  = _maybe_fresh(request, "analytics:payroll_components", compute_payroll_components, 900)
        ar,  src_a  = _maybe_fresh(request, "analytics:attrition_top", compute_attrition_top, 900)

        resp = Response({
            "kpis": kpis,
            "headcount": hc,
            "leave_series": ls,
            "leave_sla": sla,
            "payroll_components": pc,
            "attrition_top": ar,
            "_sources": {
                "kpis": src_k, "headcount": src_h, "leave_series": src_ls,
                "leave_sla": src_s, "payroll_components": src_p, "attrition_top": src_a
            }
        })
        resp["X-Analytics-Source"] = "mixed"
        return resp
