# leave/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import LeaveRequest
from notifications.tasks import send_notification
from authentication.models import User
from employee.models import Employee
from .models import *

import logging
logger = logging.getLogger(__name__)

# @shared_task
# def notify_leave_request_submission(leave_request_id):
#     """Notify manager and HR when a leave request is submitted."""
#     try:
#         leave = LeaveRequest.objects.get(id=leave_request_id)
#         employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
#         message = (
#             f"New leave request from {employee_name} for {leave.leave_type.name} "
#             f"from {leave.start_date} to {leave.end_date}."
#         )

#         # Notify the employee’s manager
#         if leave.employee.manager:
#             send_notification.delay(
#                 user_id=leave.employee.manager.user.id,
#                 message=message
#             )

#         # Notify HR and ADMIN users
#         hr_users = User.objects.filter(role__in=['HR', 'ADMIN'])
#         for hr_user in hr_users:
#             send_notification.delay(
#                 user_id=hr_user.id,
#                 message=message
#             )

#         # Notify employee of submission confirmation
#         confirmation_message = (
#             f"Your leave request for {leave.leave_type.name} "
#             f"from {leave.start_date} to {leave.end_date} has been submitted."
#         )
#         send_notification.delay(
#             user_id=leave.employee.user.id,
#             message=confirmation_message
#         )
#     except Exception as e:
#         logger.error(f"Failed to notify leave request submission {leave_request_id}: {str(e)}")

# @shared_task
# def notify_leave_request_response(leave_request_id):
#     """Notify employee and HR (if approved) of manager/HR response."""
#     try:
#         leave = LeaveRequest.objects.get(id=leave_request_id)
#         employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
#         leave_type = leave.leave_type.name
#         start_date = leave.start_date
#         end_date = leave.end_date
#         status = leave.status
#         rejection_reason = leave.rejection_reason or "No reason provided"

#         if status in ['manager_approved', 'hr_approved']:
#             message = (
#                 f"Your leave request for {leave_type} from {start_date} to {end_date} "
#                 f"has been {status.replace('_', ' ').title()}."
#             )
#         elif status == 'rejected':
#             message = (
#                 f"Your leave request for {leave_type} from {start_date} to {end_date} "
#                 f"was rejected. Reason: {rejection_reason}."
#             )
#         else:
#             return

#         # Notify the employee
#         send_notification.delay(
#             user_id=leave.employee.user.id,
#             message=message
#         )

#         # Notify HR if manager approved
#         if status == 'manager_approved':
#             hr_message = (
#                 f"Leave request from {employee_name} for {leave_type} "
#                 f"from {start_date} to {end_date} has been approved by manager."
#             )
#             hr_users = User.objects.filter(role__in=['HR', 'ADMIN'])
#             for hr_user in hr_users:
#                 send_notification.delay(
#                     user_id=hr_user.id,
#                     message=hr_message
#                 )
#     except Exception as e:
#         logger.error(f"Failed to notify leave request response {leave_request_id}: {str(e)}")

# @shared_task
# def notify_leave_balance_update(employee_id, leave_type_id, year, new_balance):
#     """Notify employee of leave balance update after HR approval."""
#     try:
#         employee = Employee.objects.get(id=employee_id)
#         leave_type = LeaveType.objects.get(id=leave_type_id)
#         message = (
#             f"Your {leave_type.name} balance for {year} has been updated to {new_balance} days."
#         )
#         send_notification.delay(
#             user_id=employee.user.id,
#             message=message
#         )
#     except Exception as e:
#         logger.error(f"Failed to notify leave balance update for employee {employee_id}: {str(e)}")

# @shared_task
# def upcoming_leave_reminder():
#     """Notify when a leave is about to end but not marked taken."""
#     try:
#         today = timezone.localdate()
#         in_five_days = today + timezone.timedelta(days=5)
#         leaves = LeaveRequest.objects.filter(
#             status='hr_approved',
#             end_date=in_five_days,
#             is_half_day=False
#         )
#         for leave in leaves:
#             employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
#             message = (
#                 f"Reminder: Leave for {employee_name} ({leave.leave_type.name}) "
#                 f"ends on {leave.end_date}. Ensure proper return to work."
#             )

#             # Notify the employee
#             send_notification.delay(
#                 user_id=leave.employee.user.id,
#                 message=message
#             )

#             # Notify the manager
#             if leave.employee.manager:
#                 send_notification.delay(
#                     user_id=leave.employee.manager.user.id,
#                     message=message
#                 )

#             # Notify HR
#             hr_users = User.objects.filter(role__in=['HR', 'ADMIN'])
#             for hr_user in hr_users:
#                 send_notification.delay(
#                     user_id=hr_user.id,
#                     message=message
#                 )
#     except Exception as e:
#         logger.error(f"Failed to send upcoming leave reminders: {str(e)}")

# @shared_task
# def notify_overlapping_leave(leave_request_id):
#     """Notify HR if a new leave request overlaps with existing approved leaves."""
#     try:
#         leave = LeaveRequest.objects.get(id=leave_request_id)
#         overlapping_leaves = LeaveRequest.objects.filter(
#             employee=leave.employee,
#             status='hr_approved',
#             start_date__lte=leave.end_date,
#             end_date__gte=leave.start_date
#         ).exclude(id=leave.id)
#         if overlapping_leaves.exists():
#             employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
#             message = (
#                 f"Warning: New leave request from {employee_name} for {leave.leave_type.name} "
#                 f"from {leave.start_date} to {leave.end_date} overlaps with existing approved leaves."
#             )
#             hr_users = User.objects.filter(role__in=['HR', 'ADMIN'])
#             for hr_user in hr_users:
#                 send_notification.delay(
#                     user_id=hr_user.id,
#                     message=message
#                 )
#     except Exception as e:
#         logger.error(f"Failed to notify overlapping leave for request {leave_request_id}: {str(e)}")
        
# @shared_task
# def notify_delegate_leave(leave_request_id):
#     leave = LeaveRequest.objects.get(id=leave_request_id)
#     delegations = Delegation.objects.filter(
#         delegator=leave.employee,
#         start_date__lte=leave.start_date,
#         end_date__gte=leave.start_date
#     )
#     for delegation in delegations:
#         message = (
#             f"Leave request submitted by {leave.employee} for {leave.leave_type.name} "
#             f"from {leave.start_date} to {leave.end_date} during your delegation."
#         )
#         send_notification.delay(
#             user_id=delegation.delegate.user.id,
#             message=message
#         )





# leave/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from authentication.models import User
from employee.models import Employee
from .models import LeaveRequest, LeaveType, Delegation

from notifications.tasks import send_notification  # assumes the task accepts kwargs like title/category/priority/metadata

import logging
logger = logging.getLogger(__name__)

LEAVE_CATEGORY = "leave"


# ---------- helpers ----------
def _fmt_d(d):
    return d.strftime("%d/%m/%Y") if d else "—"

def _deeplink(leave_id: int) -> str:
    """
    Return a UI deeplink for the leave detail (adjust if your route differs).
    """
    return f"/leaves/requests/{leave_id}/"

def _notify(user, *, title: str, message: str, priority: int = 3, leave: LeaveRequest | None = None, extra_meta: dict | None = None):
    """
    Thin wrapper around send_notification to keep all leave notifications uniform.
    """
    if not user:
        return
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        logger.warning(f"Invalid priority {priority} for notification to user {user.id}, defaulting to 3")
        priority = 3
        
    meta = {
        "deeplink": _deeplink(leave.id) if leave else None,
        "leave_id": getattr(leave, "id", None),
        "status": getattr(leave, "status", None),
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
            category=LEAVE_CATEGORY,
            priority=priority,
            metadata=meta,
        )
    except Exception as e:
        logger.error("Failed to enqueue notification to user=%s: %s", getattr(user, "id", None), e)


# ---------- tasks ----------
@shared_task
def notify_leave_request_submission(leave_request_id: int):
    """
    Notify manager + HR/ADMIN when an employee submits a leave request.
    Also send a confirmation to the employee.
    """
    try:
        leave = LeaveRequest.objects.select_related("employee", "leave_type", "employee__manager", "employee__user").get(id=leave_request_id)
        employee = leave.employee
        employee_name = f"{employee.first_name} {employee.last_name}"
        lt = leave.leave_type.name if leave.leave_type_id else "Leave"
        start, end = _fmt_d(leave.start_date), _fmt_d(leave.end_date)

        # manager / HR message
        mgmt_msg = f"Nouvelle demande de congé — {employee_name} a demandé {lt} du {start} au {end}."
        # confirmation to employee
        emp_msg = f"Votre demande de congé ({lt}) du {start} au {end} a été soumise."

        # Manager
        if getattr(employee, "manager", None) and getattr(employee.manager, "user", None):
            _notify(
                employee.manager.user,
                title="Nouvelle demande de congé",
                message=mgmt_msg,
                priority=2,
                leave=leave,
            )

        # HR / ADMIN
        for hr in User.objects.filter(role__in=["HR", "ADMIN"]):
            _notify(
                hr,
                title="Nouvelle demande de congé",
                message=mgmt_msg,
                priority=2,
                leave=leave,
            )

        # Employee confirmation
        if getattr(employee, "user", None):
            _notify(
                employee.user,
                title="Confirmation — Demande envoyée",
                message=emp_msg,
                priority=3,
                leave=leave,
            )
    except Exception as e:
        logger.error("notify_leave_request_submission(%s) failed: %s", leave_request_id, e)


@shared_task
def notify_leave_request_response(leave_request_id: int):
    """
    Notify employee of the manager/HR decision.
    If manager approved, ping HR/ADMIN for the next step.
    """
    try:
        leave = LeaveRequest.objects.select_related("employee", "leave_type", "employee__user").get(id=leave_request_id)
        employee = leave.employee
        employee_name = f"{employee.first_name} {employee.last_name}"
        lt = leave.leave_type.name if leave.leave_type_id else "Leave"
        start, end = _fmt_d(leave.start_date), _fmt_d(leave.end_date)
        status = leave.status or ""
        rejection_reason = leave.rejection_reason or "Aucune raison fournie"

        if status in ("manager_approved", "hr_approved"):
            label = "approuvée par le manager" if status == "manager_approved" else "approuvée par RH"
            title = "Demande de congé approuvée"
            msg = f"Votre demande de congé ({lt}) du {start} au {end} a été {label}."
        elif status == "rejected":
            title = "Demande de congé rejetée"
            msg = f"Votre demande de congé ({lt}) du {start} au {end} a été rejetée. Motif: {rejection_reason}."
        else:
            return  # no outgoing notification for other statuses

        # Employee
        if getattr(employee, "user", None):
            _notify(employee.user, title=title, message=msg, priority=2, leave=leave)

        # If manager approved, let HR/ADMIN know
        if status == "manager_approved":
            hr_msg = (
                f"Demande de congé approuvée par le manager — {employee_name}, {lt} du {start} au {end}. "
                f"En attente de validation RH."
            )
            for hr in User.objects.filter(role__in=["HR", "ADMIN"]):
                _notify(hr, title="Validation RH requise", message=hr_msg, priority=2, leave=leave)
    except Exception as e:
        logger.error("notify_leave_request_response(%s) failed: %s", leave_request_id, e)


@shared_task
def notify_leave_balance_update(employee_id: int, leave_type_id: int, year: int, new_balance: float):
    """
    Notify employee after HR updates the balance.
    """
    try:
        employee = Employee.objects.select_related("user").get(id=employee_id)
        lt = LeaveType.objects.get(id=leave_type_id)
        msg = f"Votre solde de {lt.name} pour {year} a été mis à jour à {new_balance} jours."
        if getattr(employee, "user", None):
            _notify(employee.user, title="Solde de congés mis à jour", message=msg, priority=3, leave=None, extra_meta={"year": year, "leave_type_id": leave_type_id})
    except Exception as e:
        logger.error("notify_leave_balance_update(emp=%s, lt=%s) failed: %s", employee_id, leave_type_id, e)


@shared_task
def upcoming_leave_reminder():
    """
    Remind employee/manager/HR 5 days before a leave ends (still approved).
    """
    try:
        today = timezone.localdate()
        in_five_days = today + timezone.timedelta(days=5)

        leaves = LeaveRequest.objects.select_related("employee", "employee__user", "employee__manager", "leave_type").filter(
            status="hr_approved",
            end_date=in_five_days,
            is_half_day=False,
        )

        for leave in leaves:
            employee = leave.employee
            employee_name = f"{employee.first_name} {employee.last_name}"
            lt = leave.leave_type.name if leave.leave_type_id else "Leave"
            msg = f"Rappel: le congé ({lt}) de {employee_name} se termine le {_fmt_d(leave.end_date)}."

            # Employee
            if getattr(employee, "user", None):
                _notify(employee.user, title="Rappel — Fin de congé", message=msg, priority=3, leave=leave)

            # Manager
            if getattr(employee, "manager", None) and getattr(employee.manager, "user", None):
                _notify(employee.manager.user, title="Rappel — Fin de congé (équipe)", message=msg, priority=3, leave=leave)

            # HR / ADMIN
            for hr in User.objects.filter(role__in=["HR", "ADMIN"]):
                _notify(hr, title="Rappel — Fin de congé", message=msg, priority=4, leave=leave)
    except Exception as e:
        logger.error("upcoming_leave_reminder failed: %s", e)


@shared_task
def notify_overlapping_leave(leave_request_id: int):
    """
    Alert HR/ADMIN if a new request overlaps an existing approved leave for the same employee.
    """
    try:
        leave = LeaveRequest.objects.select_related("employee", "leave_type").get(id=leave_request_id)

        overlapping = LeaveRequest.objects.filter(
            employee=leave.employee,
            status="hr_approved",
            start_date__lte=leave.end_date,
            end_date__gte=leave.start_date,
        ).exclude(id=leave.id)

        if overlapping.exists():
            employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
            lt = leave.leave_type.name if leave.leave_type_id else "Leave"
            start, end = _fmt_d(leave.start_date), _fmt_d(leave.end_date)
            msg = f"Attention: demande de congé ({lt}) du {start} au {end} pour {employee_name} chevauche des congés approuvés existants."

            for hr in User.objects.filter(role__in=["HR", "ADMIN"]):
                _notify(hr, title="Alerte — Chevauchement de congés", message=msg, priority=2, leave=leave)
    except Exception as e:
        logger.error("notify_overlapping_leave(%s) failed: %s", leave_request_id, e)


@shared_task
def notify_delegate_leave(leave_request_id: int):
    """
    Inform delegates if a request falls within an active delegation period.
    """
    try:
        leave = LeaveRequest.objects.select_related("employee", "leave_type").get(id=leave_request_id)
        lt = leave.leave_type.name if leave.leave_type_id else "Leave"

        delegations = Delegation.objects.select_related("delegate", "delegate__user").filter(
            delegator=leave.employee,
            start_date__lte=leave.start_date,
            end_date__gte=leave.start_date,
        )

        for d in delegations:
            msg = (
                f"Demande de congé soumise par {leave.employee} ({lt}) "
                f"du {_fmt_d(leave.start_date)} au {_fmt_d(leave.end_date)} pendant votre période de délégation."
            )
            if getattr(d.delegate, "user", None):
                _notify(d.delegate.user, title="Délégation — Nouvelle demande de congé", message=msg, priority=3, leave=leave)
    except Exception as e:
        logger.error("notify_delegate_leave(%s) failed: %s", leave_request_id, e)






