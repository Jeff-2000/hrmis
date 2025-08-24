# payroll/tasks.py
from celery import shared_task
from django.conf import settings
from django.urls import reverse
import logging

from payroll.models import PayrollRun, Payslip
from notifications.tasks import send_notification  # <- your Celery task

logger = logging.getLogger(__name__)


def _notify_payroll(user_id, message, title=None, priority=3):
    """
    Thin wrapper around send_notification for payroll notifications.
    Ensures title and priority are always set.
    """
    send_notification.delay(
        user_id=user_id,
        message=message,
        title=title or "Notification paie",
        priority=priority
    )

def _site_url() -> str:
    # Optional; set SITE_URL="http://127.0.0.1:8000" in settings for absolute links
    return (getattr(settings, "SITE_URL", "") or "").rstrip("/")


def _abs_url(relative: str) -> str:
    base = _site_url()
    return f"{base}{relative}" if base else relative


def _payslip_url(p: Payslip) -> str:
    try:
        rel = reverse("payroll_payslip_detail", kwargs={"payslip_id": p.id})
    except Exception:
        rel = f"/api/v1/payroll/payslips/{p.id}/"
    return _abs_url(rel)


def _my_payslips_url() -> str:
    try:
        rel = reverse("my_payslips")
    except Exception:
        rel = "/api/v1/payroll/me/payslips/"
    return _abs_url(rel)


@shared_task
def notify_run_generated(run_id: int, actor_id: int, count: int) -> bool:
    """Message to the user who clicked 'Generate'."""
    try:
        run = PayrollRun.objects.select_related("company_policy").get(id=run_id)
        period = f"{str(run.month).zfill(2)}/{run.year}"
        msg = f"Lot de paie {period} — politique {run.company_policy.name} généré. {count} bulletins créés/actualisés."
        
        # send_notification.delay(actor_id, msg)
        _notify_payroll(actor_id, msg, title=f"Lot de paie {period}")

        return True
    except Exception as e:
        logger.exception("notify_run_generated failed: %s", e)
        return False


@shared_task
def notify_employees_payslips_ready(run_id: int) -> dict:
    """Notify each employee that their payslip is available (after Generate)."""
    run = PayrollRun.objects.get(id=run_id)
    slips = run.payslips.select_related("employee__user", "currency").all()

    sent = 0
    skipped = 0
    for p in slips:
        uid = getattr(getattr(p.employee, "user", None), "id", None)
        if not uid:
            skipped += 1
            continue
        period = f"{str(run.month).zfill(2)}/{run.year}"
        net = f"{p.net_pay} {getattr(p.currency, 'code', '') or ''}".strip()
        url = _payslip_url(p)
        msg = f"Votre bulletin de paie {period} est disponible. Net à payer : {net}. Consulter : {url}"
        try:
            # send_notification.delay(uid, msg)
            _notify_payroll(uid, msg, title=f"Bulletin de paie {period}")
            
            sent += 1
        except Exception:
            skipped += 1
            logger.exception("Failed to enqueue employee notification for payslip %s", p.id)

    return {"sent": sent, "skipped": skipped, "total": slips.count()}


@shared_task
def notify_run_closed(run_id: int, actor_id: int) -> bool:
    """
    Message to actor + notify all employees that payment has been validated (on Close).
    """
    try:
        run = PayrollRun.objects.select_related("company_policy").get(id=run_id)
        period = f"{str(run.month).zfill(2)}/{run.year}"

        # actor
        msg_actor = f"Lot de paie {period} — politique {run.company_policy.name} fermé (paiements validés)."
        # send_notification.delay(actor_id, msg_actor)
        # Actor
        _notify_payroll(actor_id, msg_actor, title=f"Lot de paie {period} — Fermeture")

        # Notify all employees with payslips in this run
        # employees
        slips = run.payslips.select_related("employee__user", "currency").all()
        link = _my_payslips_url()
        for p in slips:
            uid = getattr(getattr(p.employee, "user", None), "id", None)
            if not uid:
                continue
            net = f"{p.net_pay} {getattr(p.currency, 'code', '') or ''}".strip()
            msg = f"Paiement validé pour {period}. Net payé : {net}. Voir vos bulletins : {link}"
            # send_notification.delay(uid, msg)
            # Employees
            _notify_payroll(uid, msg, title=f"Paiement validé — {period}")

        return True
    except Exception as e:
        logger.exception("notify_run_closed failed: %s", e)
        return False


@shared_task
def notify_run_reopened(run_id: int, actor_id: int) -> bool:
    """Message to the user who clicked 'Reopen'."""
    try:
        run = PayrollRun.objects.select_related("company_policy").get(id=run_id)
        period = f"{str(run.month).zfill(2)}/{run.year}"
        msg = f"Lot de paie {period} — politique {run.company_policy.name} réouvert."
        # send_notification.delay(actor_id, msg)
        _notify_payroll(actor_id, msg, title=f"Lot de paie {period} — Réouverture")
        return True
    except Exception as e:
        logger.exception("notify_run_reopened failed: %s", e)
        return False
