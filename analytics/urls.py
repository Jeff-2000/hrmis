# analytics/urls.py
from django.urls import path
from .views import *


urlpatterns = [
    path("analytics/dashboard/", DashboardView.as_view(), name="analytics_dashboard"),
    path("analytics/kpis/", KPIView.as_view(), name="kpis"),
    path("analytics/headcount_forecast/", HeadcountForecastView.as_view(), name="headcount_forecast"),
    path("analytics/leave_forecast/", LeaveForecastView.as_view(), name="leave_forecast"),
    path("analytics/leave_sla/", LeaveSLAView.as_view(), name="leave_sla"),
    path("analytics/payroll_components/", PayrollComponentsView.as_view(), name="payroll_components"),
    path("analytics/attrition_risk/", AttritionRiskView.as_view(), name="attrition_risk"),
    path("analytics/notification_engagement/", NotificationEngagementView.as_view(), name="notification_engagement"),
]


urlpatterns += [
    path("api/summary/", SummaryView.as_view(), name="summary"),
]


