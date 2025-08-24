# audit/registry.py
from auditlog.registry import auditlog

# Documents
from documents.models import *

# Payroll
from payroll.models import *
# Core HR
from employee.models import *

from leave.models import *

from situation.models import *
from authentication.models import *
from attendance.models import *
from notifications.models import *

# Register models. You can fine-tune with exclude_fields / mask_fields / m2m_fields
auditlog.register(Document, exclude_fields=[])  # e.g. mask_fields=["content_text"]

auditlog.register(PayrollRun)
auditlog.register(Payslip)
auditlog.register(Contract)
auditlog.register(VariableInput)
auditlog.register(RecurringComponentAssignment)
auditlog.register(PayrollComponent)
auditlog.register(CompanyPolicy, m2m_fields={"active_contribs"})
auditlog.register(ContributionScheme)
auditlog.register(TaxTable)
auditlog.register(TaxBracket)

auditlog.register(Employee)
auditlog.register(Department)
auditlog.register(Grade)

auditlog.register(LeaveBalance)
auditlog.register(Delegation)
auditlog.register(LeaveRequest)

auditlog.register(Situation)

auditlog.register(NotificationPreference)
auditlog.register(Notification)
auditlog.register(User, exclude_fields=["password", "last_login", "is_superuser", "is_staff", "is_active"])
auditlog.register(AttendanceRecord)