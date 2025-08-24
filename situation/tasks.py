# situation/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Situation
from notifications.tasks import send_notification

# @shared_task
# def monitor_situations():
#     """Check administrative situations for important status changes or anomalies."""
#     today = timezone.localdate()
#     # 1. Upcoming resumption: situations ending in 5 days
#     upcoming = Situation.objects.filter(end_date=today + timezone.timedelta(days=5), status='actif')
#     for sit in upcoming:
#         msg = f"{sit.situation_type.name} for {sit.employee} ends on {sit.end_date}. Ensure resumption process."
#         send_notification.delay(sit.employee.contact, "SMS", msg)
#     # 2. Ended but not closed: situations where end_date passed but status still 'actif'
#     overdue = Situation.objects.filter(end_date__lt=today, status='actif')
#     for sit in overdue:
#         msg = f"Situation {sit.situation_type.name} for {sit.employee} should have ended on {sit.end_date} but is not closed."
#         send_notification.delay(None, "EMAIL", msg)  # notify HR via email
#         sit.status = 'terminé'
#         sit.save()
#     # 3. Death reported but still active
#     deaths = Situation.objects.filter(situation_type__code='exit').exclude(exit_type__in=[None, '']).select_related('employee')
#     for sit in deaths:
#         if 'décès' in sit.exit_type.lower() and sit.employee.is_active:
#             msg = f"Alert: {sit.employee} marked as deceased on {sit.start_date} but still active in system."
#             send_notification.delay(None, "WHATSAPP", msg)
#             sit.employee.is_active = False
#             sit.employee.save()




# situation/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from authentication.models import User
from .models import Situation
from notifications.tasks import send_notification

import logging
logger = logging.getLogger(__name__)

SITUATION_CATEGORY = "situation"

def _fmt_d(d):
    return d.strftime("%d/%m/%Y") if d else "—"

@shared_task
def monitor_situations():
    """
    Watch administrative situations and notify stakeholders.

    Rules
    -----
    1) Upcoming end in 5 days (status='actif'):
       - Notify employee, manager, HR/ADMIN.
       - If situation_type.suspend_payroll is True, include payroll reminder in metadata/message.

    2) Overdue closure (end_date < today AND status='actif'):
       - Alert HR/ADMIN to close.
       - Auto-mark status='terminé'. If suspend_payroll=True, include resume-payroll reminder.

    3) Exit by death (situation_type.code == 'exit' and exit_type indicates 'décès'):
       - Alert HR/ADMIN if employee remains active, then deactivate employee.
    """
    try:
        today = timezone.localdate()
        in_five_days = today + timezone.timedelta(days=5)

        qs = Situation.objects.select_related(
            "employee",
            "employee__user",
            "employee__manager",
            "employee__manager__user",
            "situation_type",
        )

        # Cache HR/ADMIN recipients once
        hr_admin_users = list(User.objects.filter(role__in=["HR", "ADMIN"]).only("id"))

        # 1) Upcoming end in 5 days (still active)
        upcoming = qs.filter(status="actif", end_date=in_five_days)
        for sit in upcoming:
            employee = sit.employee
            emp_user = getattr(employee, "user", None)
            mgr_user = getattr(getattr(employee, "manager", None), "user", None)
            st_name = sit.situation_type.name
            st_code = (sit.situation_type.code or "").lower()
            needs_payroll_suspend = bool(sit.situation_type.suspend_payroll)
            end_s = _fmt_d(sit.end_date)

            payroll_hint = (
                " (⚠︎ reprise de paie à préparer)" if needs_payroll_suspend else ""
            )

            # Employee reminder
            if emp_user:
                send_notification.delay(
                    user_id=emp_user.id,
                    title="Rappel — Fin de situation",
                    message=f"Votre {st_name} se termine le {end_s}.{payroll_hint}",
                    category=SITUATION_CATEGORY,
                    priority=3,
                    metadata={"situation_id": sit.id, "situation_code": st_code, "suspend_payroll": needs_payroll_suspend},
                )

            # Manager reminder
            if mgr_user:
                send_notification.delay(
                    user_id=mgr_user.id,
                    title="Rappel — Fin de situation (équipe)",
                    message=f"{st_name} de {employee} se termine le {end_s}. Préparez la reprise administrative.{payroll_hint}",
                    category=SITUATION_CATEGORY,
                    priority=3,
                    metadata={"situation_id": sit.id, "situation_code": st_code, "suspend_payroll": needs_payroll_suspend},
                )

            # HR / ADMIN reminder (+ payroll hint if applicable)
            hr_msg = f"{st_name} de {employee} se termine le {end_s}. Veuillez préparer la reprise.{payroll_hint}"
            for hr in hr_admin_users:
                send_notification.delay(
                    user_id=hr.id,
                    title="Rappel — Fin de situation",
                    message=hr_msg,
                    category=SITUATION_CATEGORY,
                    priority=3,
                    metadata={"situation_id": sit.id, "situation_code": st_code, "suspend_payroll": needs_payroll_suspend},
                )

        # 2) Ended but not closed: end_date passed but status still 'actif'
        overdue = qs.filter(status="actif", end_date__lt=today)
        for sit in overdue:
            st_name = sit.situation_type.name
            st_code = (sit.situation_type.code or "").lower()
            needs_payroll_suspend = bool(sit.situation_type.suspend_payroll)
            end_s = _fmt_d(sit.end_date)

            resume_hint = " Reprendre la paie si elle avait été suspendue." if needs_payroll_suspend else ""

            msg = (
                f"La situation {st_name} pour {sit.employee} aurait dû se terminer le {end_s} "
                f"mais est toujours marquée 'actif'.{resume_hint}"
            )
            for hr in hr_admin_users:
                send_notification.delay(
                    user_id=hr.id,
                    title="Alerte — Situation à clôturer",
                    message=msg,
                    category=SITUATION_CATEGORY,
                    priority=2,
                    metadata={"situation_id": sit.id, "situation_code": st_code, "suspend_payroll": needs_payroll_suspend},
                )

            # Auto-close to keep the dataset consistent
            sit.status = "terminé"
            sit.save(update_fields=["status"])

        # 3) Death reported but employee still active
        deaths = qs.filter(
            situation_type__code__iexact="exit"
        ).exclude(
            exit_type__in=[None, ""]
        ).filter(
            Q(exit_type__iexact="décès") | Q(exit_type__icontains="deces") | Q(exit_type__icontains="décès")
        )

        for sit in deaths:
            employee = sit.employee
            # Some projects use employee.is_active (boolean field); others a property.
            # We guard both: default to True if missing.
            if getattr(employee, "is_active", True):
                msg = (
                    f"Alerte: {employee} déclaré décédé le {_fmt_d(sit.start_date)} "
                    f"mais toujours actif dans le système."
                )
                for hr in hr_admin_users:
                    send_notification.delay(
                        user_id=hr.id,
                        title="Alerte — Décès vs statut actif",
                        message=msg,
                        category=SITUATION_CATEGORY,
                        priority=1,
                        metadata={"situation_id": sit.id, "employee_id": str(getattr(employee, 'id', None)), "situation_code": "exit"},
                    )
                try:
                    employee.is_active = False
                    employee.save(update_fields=["is_active"])
                except Exception as e:
                    logger.error("Failed to deactivate employee %s after death alert: %s", employee, e)

    except Exception as e:
        logger.exception("monitor_situations failed: %s", e)
