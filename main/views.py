from django.shortcuts import render, redirect

# Create your views here.

def main_view(request):
    # This is a placeholder for the main view logic
    return render(request, 'main/index.html')

def homeFakeView(request):
    # This is a placeholder for the home fake view logic
    return render(request, 'main/homeFake.html')


def home_view(request):
    # This is a placeholder for the home fake view logic
    return render(request, 'main/home.html')

def profile_view(request):
    # This is a placeholder for the home fake view logic
    return render(request, 'main/profile.html')

def settings_view(request):
    # This is a placeholder for the settings view logic
    return render(request, 'main/settings.html')

def help_view(request):
    # This is a placeholder for the help view logic
    return render(request, 'main/help.html')

def fakebase_view(request):
    # This is a placeholder for the fake base view logic
    return render(request, 'main/fakebase.html')


################################################################################
########################### Dashboard Views ###########################
################################################################################
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from authentication.models import User
from employee.models import *
from documents.models import *
from leave.models import *
from situation.models import *
from notifications.models import *
from payroll.models import Contract

# Optional payroll imports (handles both simple Payroll and advanced Run/Payslip)
try:
    from payroll.models import PayrollRun, Payslip
    HAS_RUN = True
except Exception:
    PayrollRun = None
    Payslip = None
    HAS_RUN = False

# Optional auditlog import
try:
    from auditlog.models import LogEntry as AuditLogEntry
    HAS_AUDIT = True
except Exception:
    AuditLogEntry = None
    HAS_AUDIT = False


class DashboardPageView(TemplateView):
    template_name = "main/dashboard.html"

    def get_context_data(self, **kwargs):
        # Minimal server-side context (we fetch data via JS from /dashboard/api/summary/)
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Tableau de bord"
        return ctx


class DashboardSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = (user.role or "").upper()
        now = timezone.now()
        today = now.date()

        # ---------- KPI COUNTS ----------
        headcount_total = Employee.objects.count()
        # "Active" proxy: status='actif' if use that
        headcount_active = Employee.objects.filter(status__iexact="actif").count()

        contracts_expiring_30d = Contract.objects.filter(
            status="ACTIVE",
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30),
        ).count()

        documents_to_validate = Document.objects.filter(status="to_validate").count()


# class DashboardSummaryAPI(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         role = (user.role or "").upper()
#         now = timezone.now()
#         today = now.date()

#         # ---------- KPI COUNTS ----------
#         headcount_total = Employee.objects.count()
#         headcount_active = Employee.objects.filter(status__iexact="actif").count()

#         contracts_expiring_30d = Contract.objects.filter(
#             status="ACTIVE",
#             end_date__isnull=False,
#             end_date__gte=today,
#             end_date__lte=today + timedelta(days=30),
#         ).count()

#         documents_to_validate = Document.objects.filter(status="to_validate").count()

#         # ✅ Build response payload
#         data = {
#             "headcount": {
#                 "total": headcount_total,
#                 "active": headcount_active,
#             },
#             "contracts": {
#                 "expiring_30d": contracts_expiring_30d,
#             },
#             "documents": {
#                 "to_validate": documents_to_validate,
#             },
#             "user_role": role,
#         }

#         # ✅ Return Response
#         return Response(data)
    
    

# dashboard/views.py
from datetime import timedelta  # <-- add this
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from authentication.models import User



# Optional payroll imports
try:
    from payroll.models import PayrollRun, Payslip
    HAS_RUN = True
except Exception:
    PayrollRun = None
    Payslip = None
    HAS_RUN = False

# Optional auditlog import
try:
    from auditlog.models import LogEntry as AuditLogEntry
    HAS_AUDIT = True
except Exception:
    AuditLogEntry = None
    HAS_AUDIT = False


class DashboardPageView(TemplateView):
    template_name = "main/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Tableau de bord"
        return ctx


class DashboardSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = (user.role or "").upper()
        now = timezone.now()
        today = now.date()

        # ---------- KPIs ----------
        headcount_total = Employee.objects.count()
        headcount_active = Employee.objects.filter(status__iexact="actif").count()
        contracts_expiring_30d = Contract.objects.filter(
            status="ACTIVE",
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30),
        ).count()
        documents_to_validate = Document.objects.filter(status="to_validate").count()
        active_situations = Situation.objects.filter(
            Q(end_date__isnull=True, start_date__lte=today) |
            Q(end_date__gte=today, start_date__lte=today)
        ).count()
        unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

        # ---------- Leave trend (12 months) ----------
        start_12m = (now - timedelta(days=365)).date().replace(day=1)
        leaves_12m = (
            LeaveRequest.objects.filter(status="hr_approved", start_date__gte=start_12m)
            .annotate(m=TruncMonth("start_date"))
            .values("m")
            .annotate(c=Count("id"))
            .order_by("m")
        )
        leave_labels = [x["m"].strftime("%Y-%m") for x in leaves_12m]
        leave_values = [x["c"] for x in leaves_12m]

        # ---------- Headcount by department ----------
        dept_top = (
            Employee.objects.values("department__name")
            .annotate(c=Count("id"))
            .order_by("-c")[:8]
        )
        dept_labels = [d["department__name"] or "—" for d in dept_top]
        dept_values = [d["c"] for d in dept_top]

        # ---------- Role-specific leave counters ----------
        my_employee = getattr(user, "employee", None)
        my_leave_pending = LeaveRequest.objects.filter(
            employee=my_employee, status="pending"
        ).count() if my_employee else 0

        manager_to_approve = 0
        if role == "MANAGER" and my_employee:
            manager_to_approve = LeaveRequest.objects.filter(
                status="pending", employee__manager=my_employee
            ).count()

        hr_to_approve = 0
        if role in ("HR", "ADMIN"):
            hr_to_approve = LeaveRequest.objects.filter(status="manager_approved").count()

        # ---------- Payroll (optional) ----------
        payroll = {"has_run": HAS_RUN}
        if HAS_RUN:
            latest_run = PayrollRun.objects.order_by("-year", "-month", "-id").first()
            if latest_run:
                payroll["latest_run"] = {
                    "id": latest_run.id,
                    "year": latest_run.year,
                    "month": latest_run.month,
                    "status": latest_run.status,
                }
                if my_employee and Payslip:
                    recent_my = (
                        Payslip.objects.filter(employee=my_employee)
                        .select_related("run")
                        .order_by("-run__year", "-run__month")[:3]
                    )
                    payroll["my_payslips"] = [
                        {
                            "id": p.id,
                            "period": f"{p.run.month:02d}/{p.run.year}",
                            "net_pay": str(p.net_pay),
                            "finalized": bool(p.finalized),
                        }
                        for p in recent_my
                    ]

        # ---------- Recents ----------
        recent_notifications = list(
            Notification.objects.filter(user=user)
            .order_by("-timestamp")
            .values("id", "title", "message", "status", "is_read", "timestamp")[:5]
        )

        recent_leaves_qs = LeaveRequest.objects.all().order_by("-requested_at")
        if role == "MANAGER" and my_employee:
            recent_leaves_qs = recent_leaves_qs.filter(employee__manager=my_employee)
        elif role not in ("HR", "ADMIN"):
            recent_leaves_qs = recent_leaves_qs.filter(employee=my_employee) if my_employee else recent_leaves_qs.none()

        recent_leaves = [
            {
                "id": l.id,
                "employee": f"{l.employee.first_name} {l.employee.last_name}",
                "type": l.leave_type.name,
                "start": l.start_date.isoformat(),
                "end": l.end_date.isoformat(),
                "status": l.status,
            }
            for l in recent_leaves_qs[:5]
        ]

        recent_audit = []
        if HAS_AUDIT:
            recent_audit = list(
                AuditLogEntry.objects.order_by("-timestamp")
                .values("id", "actor_id", "content_type_id", "object_pk", "action", "timestamp")[:5]
            )

        birthdays = list(
            Employee.objects.filter(date_of_birth__month=today.month)
            .values("id", "first_name", "last_name", "date_of_birth")[:8]
        )

        data = {
            "user": {"id": user.id, "role": role, "name": user.get_full_name() or user.username},
            "kpis": {
                "headcount_total": headcount_total,
                "headcount_active": headcount_active,
                "contracts_expiring_30d": contracts_expiring_30d,
                "documents_to_validate": documents_to_validate,
                "situations_active": active_situations,
                "unread_notifications": unread_notifications,
            },
            "leave": {
                "my_pending": my_leave_pending,
                "manager_to_approve": manager_to_approve,
                "hr_to_approve": hr_to_approve,
                "trend": {"labels": leave_labels, "values": leave_values},
            },
            "headcount": {"by_department": {"labels": dept_labels, "values": dept_values}},
            "payroll": payroll,
            "recent": {
                "notifications": recent_notifications,
                "leaves": recent_leaves,
                "audit": recent_audit,
                "birthdays_this_month": birthdays,
            },
        }
        return Response(data)  # <-- DO NOT forget `return`



# fas fa-gauge-high
        # ---------- EMPLOYEE STATISTICS ----------
        
############################ Public Page View ###########
# Public Page
def public_home(request):
    # If user is authenticated, redirect to home dashboard
    try:
        if request.user.is_authenticated:
            return redirect('home_dashboard')
    except AttributeError:
        pass
    # Render the public home page
    return render(request, 'main/public_home.html')
##########################################################
from django.contrib.auth import logout
from django.shortcuts import redirect
# Logout view
def logout_view(request):
    logout(request)  # ✅ removes the user from the session
    return redirect("public_home")  # or "home", or wherever 

##########################################################
# System Info and Log Viewing (for staff users, DEBUG only)
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def system_info(request):
    if not settings.DEBUG:
        raise Http404("Not found")
    
    import platform
    import sys
    import django
    import celery

    info = {
        "python_version": sys.version,
        "django_version": django.get_version(),
        "celery_version": celery.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }
    return JsonResponse(info)

def view_log_file(request, filename):
    file_path = settings.BASE_DIR / filename
    if file_path.exists():
        with open(file_path, 'r') as file:
            response = HttpResponse(file.read(), content_type='text/plain')
            return response
    else:
        raise Http404("Log file does not exist")

##########################################################
