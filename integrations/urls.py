# from django.urls import path, include
# from .views import (
#     PayrollUploadJWTView,
#     PayrollDisbursementCallbackJWTView,
#     AttendancePunchJWTView,
#     AttendanceBulkJWTView,
# )

# urlpatterns = [
#     path("payroll/upload_jwt/", PayrollUploadJWTView.as_view(), name="integrations-payroll-upload-jwt"),
#     path("payroll/disbursement_callback_jwt/", PayrollDisbursementCallbackJWTView.as_view(), name="integrations-payroll-disbursement-callback-jwt"),
#     path("attendance/punch_jwt/", AttendancePunchJWTView.as_view(), name="integrations-attendance-punch-jwt"),
#     path("attendance/bulk_jwt/", AttendanceBulkJWTView.as_view(), name="integrations-attendance-bulk-jwt"),
# ]


# urlpatterns += [
#     path("auth/jwt/", include(("integrations.jwt_urls", "integrations"), namespace="integrations")),
# ]


from django.urls import path, include
from .views import (
    PayrollUploadJWTView,
    PayrollDisbursementCallbackJWTView,
    AttendancePunchJWTView,
    AttendanceBulkJWTView,
)

# Give this module an app_name for clean reversing
app_name = "integrations"

urlpatterns = [
    path("payroll/upload_jwt/", PayrollUploadJWTView.as_view(), name="payroll-upload-jwt"),
    path("payroll/disbursement_callback_jwt/", PayrollDisbursementCallbackJWTView.as_view(), name="payroll-disbursement-callback-jwt"),
    path("attendance/punch_jwt/", AttendancePunchJWTView.as_view(), name="attendance-punch-jwt"),
    path("attendance/bulk_jwt/", AttendanceBulkJWTView.as_view(), name="attendance-bulk-jwt"),

    # Mount JWT token endpoints under integrations with a DISTINCT namespace
    path("auth/jwt/", include(("integrations.jwt_urls", "integrations_jwt"), namespace="integrations_jwt")),
]
