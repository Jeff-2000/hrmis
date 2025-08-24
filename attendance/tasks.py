# attendance/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import AttendanceRecord
from employee.models import Employee
from notifications.tasks import send_notification

# @shared_task
# def daily_attendance_reconciliation():
#     """Mark employees absent if they have no attendance record for today, and send alerts for prolonged absences."""
#     today = timezone.localdate()
#     # Identify employees without a record today
#     absentees = Employee.objects.exclude(attendancerecord__date=today, attendancerecord__status='present')
#     for emp in absentees:
#         # Create an absent record for today if not already present
#         rec, created = AttendanceRecord.objects.get_or_create(employee=emp, date=today)
#         rec.status = 'absent'
#         rec.save()
#         # (Optional) If the employee has been absent for 3+ consecutive days, trigger an alert
#         # Count consecutive absences (including today)
#         recent_absences = AttendanceRecord.objects.filter(employee=emp, status='absent').order_by('-date')[:5]
#         # simple check: if first 3 of recent list are consecutive days including today
#         if len(recent_absences) >= 3:
#             # Check if they are continuous dates
#             dates = [r.date for r in recent_absences[:3]]
#             if dates[0] == today and (dates[0] - dates[1]).days == 1 and (dates[1] - dates[2]).days == 1:
#                 # Send notification (simulate SMS/Email alert)
#                 message = f"Alert: {emp} has been absent for 3 consecutive days (unjustified)."
#                 send_notification.delay(emp.id, "absence_alert", message)  # Celery task for sending


from celery import shared_task
from django.utils import timezone
from django.db.models import F
from .models import AttendanceRecord
from employee.models import Employee
from authentication.models import User
from notifications.tasks import send_notification
import logging

logger = logging.getLogger(__name__)

ATTENDANCE_CATEGORY = "attendance"

# ---------- helpers ----------
def _fmt_d(d):
    """Format date as DD/MM/YYYY or return '—' if None."""
    return d.strftime("%d/%m/%Y") if d else "—"

def _deeplink(attendance_id: int) -> str:
    """
    Return a UI deeplink for the attendance record detail (adjust if your route differs).
    """
    return f"/attendance/records/{attendance_id}/"

def _notify(user, *, title: str, message: str, priority: int = 3, attendance: AttendanceRecord | None = None, extra_meta: dict | None = None):
    """
    Thin wrapper around send_notification to keep all attendance notifications uniform.
    """
    if not user:
        return
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        logger.warning(f"Invalid priority {priority} for notification to user {user.id}, defaulting to 3")
        priority = 3
        
    meta = {
        "deeplink": _deeplink(attendance.id) if attendance else None,
        "attendance_id": getattr(attendance, "id", None),
        "status": getattr(attendance, "status", None),
    }
    if extra_meta:
        meta.update(extra_meta)

    try:
        # Let the notification service pick the right channel based on user preferences.
        # If you want to force an in-app copy for all, you can also pass channel="INAPP".
        send_notification.delay(
            user_id=user.id,
            title=title,
            message=message,
            category=ATTENDANCE_CATEGORY,
            priority=priority,
            metadata=meta,
        )
    except Exception as e:
        logger.error("Failed to enqueue notification to user=%s: %s", getattr(user, "id", None), e)

@shared_task
def daily_attendance_reconciliation():
    """Mark employees absent if they have no attendance record for today, and send alerts for prolonged absences."""
    try:
        today = timezone.localdate()
        # Identify employees without a record today
        absentees = Employee.objects.exclude(attendancerecord__date=today, attendancerecord__status='present').select_related('user', 'manager', 'manager__user')

        for emp in absentees:
            # Create an absent record for today if not already present
            rec, created = AttendanceRecord.objects.get_or_create(employee=emp, date=today, defaults={'status': 'absent'})
            if not created and rec.status != 'absent':
                rec.status = 'absent'
                rec.save(update_fields=['status'])

            # Check for 3+ consecutive days of absence
            recent_absences = AttendanceRecord.objects.filter(employee=emp, status='absent').order_by('-date')[:5]
            if len(recent_absences) >= 3:
                # Check if the first 3 absences are consecutive, including today
                dates = [r.date for r in recent_absences[:3]]
                if dates[0] == today and (dates[0] - dates[1]).days == 1 and (dates[1] - dates[2]).days == 1:
                    employee_name = f"{emp.first_name} {emp.last_name}"
                    message = f"Alerte: {employee_name} est absent(e) depuis 3 jours consécutifs (non justifié) jusqu'au {_fmt_d(today)}."

                    # Notify the employee's manager
                    if getattr(emp, "manager", None) and getattr(emp.manager, "user", None):
                        _notify(
                            emp.manager.user,
                            title="Alerte d'absence prolongée",
                            message=message,
                            priority=2,
                            attendance=rec,
                            extra_meta={"employee_id": str(emp.id)},
                        )

                    # Notify all ADMIN users
                    for admin in User.objects.filter(role='ADMIN'):
                        _notify(
                            admin,
                            title="Alerte d'absence prolongée",
                            message=message,
                            priority=2,
                            attendance=rec,
                            extra_meta={"employee_id": str(emp.id)},
                        )

                    # Notify the employee (if they have a user account)
                    if getattr(emp, "user", None):
                        _notify(
                            emp.user,
                            title="Alerte d'absence",
                            message=f"Alerte: Vous êtes enregistré(e) comme absent(e) depuis 3 jours consécutifs jusqu'au {_fmt_d(today)}. Veuillez justifier votre absence.",
                            priority=2,
                            attendance=rec,
                            extra_meta={"employee_id": str(emp.id)},
                        )

    except Exception as e:
        logger.error("daily_attendance_reconciliation failed: %s", e)




