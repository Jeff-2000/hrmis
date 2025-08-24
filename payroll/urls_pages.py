# payroll/urls_pages.py (extend)

from django.urls import path
from . import views_pages as pages

urlpatterns = [
    # existing:
    path("", pages.runs_dashboard, name="payroll_list"),
    path("runs/<int:run_id>/", pages.run_detail, name="payroll_run_detail"),
    path("me/payslips/", pages.my_payslips, name="my_payslips"),
    path("payslips/<int:payslip_id>/", pages.payslip_detail, name="payroll_payslip_detail"),

    # NEW settings
    path("settings/policies/", pages.settings_policies, name="payroll_settings_policies"),
    path("settings/components/", pages.settings_components, name="payroll_settings_components"),
    path("settings/tax/", pages.settings_tax, name="payroll_settings_tax"),
    path("settings/contribs/", pages.settings_contribs, name="payroll_settings_contribs"),
    path("settings/fx/", pages.settings_fx, name="payroll_settings_fx"),
]


urlpatterns += [
    path('dashboard/data/', pages.PayrollDashboardView.as_view(), name='payroll_dashboard_data'),
    # Pages
    path('dashboard/', pages.payroll_dashboard_page, name='payroll_dashboard'),
    path('variables/', pages.payroll_variables_page, name='payroll_variables'),
    path('calendar/', pages.payroll_calendar_page, name='payroll_calendar'),
    # path('employee/<int:employee_id>/compensation/', pages.payroll_employee_compensation_page, name='payroll_employee_compensation'),
    # accept: "me", int id, or uuid/slug
    # accepts "me", int, or uuid as strings; the view will resolve it
    path('employee/<slug:employee_id>/compensation/', pages.payroll_employee_compensation_page, name='payroll_employee_compensation'),

]

urlpatterns += [
    path('payslips/all/', pages.all_payslips_page, name='payroll_all_payslips'),
]


urlpatterns += [
    path('contracts/', pages.contracts_admin_page, name='contracts_admin'),          # HR/ADMIN only
    path('contracts/my/', pages.contracts_my_page, name='contracts_my'),            # employee self-view
]
