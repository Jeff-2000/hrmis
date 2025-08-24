# documents/urls.py

# from rest_framework.routers import DefaultRouter
# from .views import PayrollRecordViewSet

# router = DefaultRouter()
# router.register(r'payroll', PayrollRecordViewSet, basename='payroll')

# urlpatterns = router.urls



# payroll/urls.py (extend router registrations)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'situation-types', SituationTypeViewSet, basename='situation-types')
router.register(r'runs', PayrollRunViewSet, basename='payroll-runs')
router.register(r'payslips', PayslipViewSet, basename='payslips')
router.register(r'components', PayrollComponentViewSet, basename='components')

# NEW
router.register(r'company-policy', CompanyPolicyViewSet, basename='company-policy')
router.register(r'currencies', CurrencyViewSet, basename='currencies')
router.register(r'exchange-rates', ExchangeRateViewSet, basename='exchange-rates')
router.register(r'tax-tables', TaxTableViewSet, basename='tax-tables')
router.register(r'tax-brackets', TaxBracketViewSet, basename='tax-brackets')
router.register(r'contribs', ContributionSchemeViewSet, basename='contribs')

router.register(r'variables', VariableInputViewSet, basename='variables')
router.register(r'recurring', RecurringComponentAssignmentViewSet, basename='recurring')
router.register(r'contracts', ContractViewSet, basename='contracts')
router.register(r'compensation', CompensationViewSet, basename='compensations')



urlpatterns = [ path('', include(router.urls)), ]

# project urls.py (or app-level urls __init__)

urlpatterns += [
    # ... other routes ...
    path("payroll/", include("payroll.urls_pages")),     # UI pages


]




