# payroll/views_pages.py
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.http import HttpResponseForbidden

@login_required
def runs_dashboard(request):
    # HR/ADMIN landing for payroll
    return render(request, "payroll/runs.html")

@login_required
def run_detail(request, run_id: int):
    return render(request, "payroll/run_detail.html", {"run_id": run_id})

@login_required
def my_payslips(request):
    # Employee self-service list
    return render(request, "payroll/my_payslips.html")

@login_required
def payslip_detail(request, payslip_id: int):
    # Works for HR/ADMIN (any payslip) and for an employee (own payslip only)
    return render(request, "payroll/payslip_detail.html", {"payslip_id": payslip_id})

# payroll/views_pages.py (extend)

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

def is_hr_admin(user):
    return (getattr(user, 'role', '') or '').upper() in ('HR','ADMIN')

@login_required
@user_passes_test(is_hr_admin)
def settings_policies(request):
    return render(request, "payroll/settings_policies.html")

@login_required
@user_passes_test(is_hr_admin)
def settings_components(request):
    return render(request, "payroll/settings_components.html")

@login_required
@user_passes_test(is_hr_admin)
def settings_tax(request):
    return render(request, "payroll/settings_tax.html")

@login_required
@user_passes_test(is_hr_admin)
def settings_contribs(request):
    return render(request, "payroll/settings_contribs.html")

@login_required
@user_passes_test(is_hr_admin)
def settings_fx(request):
    return render(request, "payroll/settings_fx.html")


# UI pages (render templates)
def payroll_dashboard_page(request):
    return render(request, 'payroll/dashboard.html')

def payroll_variables_page(request):
    return render(request, 'payroll/variables.html')

def payroll_calendar_page(request):
    return render(request, 'payroll/calendar.html')


import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def payroll_employee_compensation_page(request, employee_id: str):
    """
    Renders the UI. Accepts 'me', int id, or uuid-like slug.
    """
    return render(
        request,
        "payroll/employee_compensation.html",
        {
            # Serialize as JSON so JS can consume the raw string safely.
            "employee_id": json.dumps(employee_id),
        },
    )


from rest_framework.views import APIView
from . models import *
from . serializers import *
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import viewsets
from employee.permissions import IsAdminOrHR
from django.shortcuts import render, get_object_or_404 

class PayrollDashboardView(APIView):
    permission_classes = [IsAdminOrHR]
    def get(self, request):
        # KPIs
        total_runs = PayrollRun.objects.count()
        draft = PayrollRun.objects.filter(status=PayrollRun.DRAFT).count()
        processed = PayrollRun.objects.filter(status=PayrollRun.PROCESSED).count()
        closed = PayrollRun.objects.filter(status=PayrollRun.CLOSED).count()

        # Recent runs
        recent = PayrollRun.objects.select_related('company_policy').order_by('-year','-month')[:10]
        recent_data = PayrollRunSerializer(recent, many=True).data

        # Employees excluded by suspend situations (today)
        from situation.models import Situation
        today = timezone.localdate()
        excluded = Situation.objects.filter(
            situation_type__suspend_payroll=True,
            start_date__lte=today
        ).filter(Q(end_date__gte=today) | Q(end_date__isnull=True)).values_list('employee_id', flat=True).distinct()
        excluded_count = excluded.count()

        return Response({
            'kpis': {'total_runs': total_runs, 'draft': draft, 'processed': processed, 'closed': closed, 'excluded_today': excluded_count},
            'recent_runs': recent_data
        })



@login_required
def all_payslips_page(request):
    role = (getattr(request.user, 'role', '') or '').upper()
    if role not in ('ADMIN', 'HR'):
        raise PermissionDenied("Accès réservé à l'administration.")
    return render(request, 'payroll/all_payslips.html', {})



from django.contrib.auth.decorators import login_required, user_passes_test



def _is_hr_or_admin(user):
    return getattr(user, 'is_authenticated', False) and (getattr(user, 'role', '').upper() in ('HR','ADMIN'))

@login_required
@user_passes_test(_is_hr_or_admin)
def contracts_admin_page(request):
    # HR/ADMIN can manage all contracts
    return render(request, 'payroll/contracts_admin.html')

@login_required
def contracts_my_page(request):
    # Any employee can see their own contracts
    emp = getattr(request.user, 'employee', None)
    if not emp:
        return HttpResponseForbidden("Aucun employé associé.")
    return render(request, 'payroll/contracts_my.html', {
        'employee_id': emp.pk,  # could be int or uuid
        'can_manage': _is_hr_or_admin(request.user),
    })






