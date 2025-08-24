# documents/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from leave.models import LeaveRequest
from documents.models import Document
from .models import Document
from employee.models import Employee
from authentication.models import User
from payroll.models import Contract
from notifications.tasks import send_notification
import logging

logger = logging.getLogger(__name__)

CONTRACT_CATEGORY = "contract"


@shared_task
def check_document_expiry():
    """Mark documents as expired if their validity period has passed and notify relevant users."""
    today = timezone.localdate()
    expiring_docs = Document.objects.filter(status='valide', issuance_date__isnull=False)
    for doc in expiring_docs:
        # Example criterion: if a document is older than 1 year, consider it expired (this can be adjusted per type)
        if doc.issuance_date and (today - doc.issuance_date).days > 365:
            doc.status = 'expiré'
            doc.save()
            # # Notify the employee and HR that the document expired
            # message = f"Document {doc.id} of type {doc.document_type} has expired and needs renewal."
            # send_notification.delay(None, "document_expired", message)
            # # In a real case, we'd determine which employee this document is for and include their ID or contact.


# ---------- helpers ----------
def _fmt_d(d):
    """Format date as DD/MM/YYYY or return '—' if None."""
    return d.strftime("%d/%m/%Y") if d else "—"

def _deeplink(contract_id: str) -> str:
    """
    Return a UI deeplink for the contract detail (adjust if your route differs).
    """
    return f"/contracts/{contract_id}/"

def _notify(user, *, title: str, message: str, priority: int = 3, contract: Contract | None = None, extra_meta: dict | None = None):
    """
    Thin wrapper around send_notification to keep all contract notifications uniform.
    """
    if not user:
        return
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        logger.warning(f"Invalid priority {priority} for notification to user {user.id}, defaulting to 3")
        priority = 3
        
    meta = {
        "deeplink": _deeplink(contract.id) if contract else None,
        "contract_id": str(getattr(contract, "id", None)),
        "status": getattr(contract, "status", None),
    }
    if extra_meta:
        meta.update(extra_meta)

    try:
        send_notification.delay(
            user_id=user.id,
            title=title,
            message=message,
            category=CONTRACT_CATEGORY,
            priority=priority,
            metadata=meta,
        )
    except Exception as e:
        logger.error("Failed to enqueue notification to user=%s: %s", getattr(user, "id", None), e)

@shared_task
def check_contract_expiry():
    """Mark contracts as expired if their end_date has passed and notify the employee's manager and ADMIN users."""
    try:
        today = timezone.localdate()
        # Find active contracts with an end_date before today
        expiring_contracts = Contract.objects.filter(
            status='ACTIVE',
            end_date__isnull=False,
            end_date__lt=today
        ).select_related('employee', 'employee__user', 'employee__manager', 'employee__manager__user', 'document')

        for contract in expiring_contracts:
            # Update contract status to EXPIRED
            contract.status = 'EXPIRED'
            contract.save(update_fields=['status'])

            # Update associated document status to 'expiré' if it exists
            if contract.document:
                contract.document.status = 'expiré'
                contract.document.save(update_fields=['status'])

            employee_name = f"{contract.employee.first_name} {contract.employee.last_name}"
            message = (
                f"Alerte: Le contrat {contract.contract_type} de {employee_name} "
                f"(du {_fmt_d(contract.start_date)} au {_fmt_d(contract.end_date)}) a expiré. "
                f"Veuillez examiner et renouveler si nécessaire."
            )

            # Notify the employee's manager
            if getattr(contract.employee, "manager", None) and getattr(contract.employee.manager, "user", None):
                _notify(
                    contract.employee.manager.user,
                    title="Alerte — Contrat expiré",
                    message=message,
                    priority=2,
                    contract=contract,
                    extra_meta={"employee_id": str(contract.employee.id)},
                )

            # Notify all ADMIN users
            for admin in User.objects.filter(role='ADMIN'):
                _notify(
                    admin,
                    title="Alerte — Contrat expiré",
                    message=message,
                    priority=2,
                    contract=contract,
                    extra_meta={"employee_id": str(contract.employee.id)},
                )

            # Notify the employee (if they have a user account)
            if getattr(contract.employee, "user", None):
                _notify(
                    contract.employee.user,
                    title="Alerte — Contrat expiré",
                    message=f"Alerte: Votre contrat {contract.contract_type} (du {_fmt_d(contract.start_date)} au {_fmt_d(contract.end_date)}) a expiré. Veuillez contacter HR pour renouvellement.",
                    priority=2,
                    contract=contract,
                    extra_meta={"employee_id": str(contract.employee.id)},
                )

    except Exception as e:
        logger.error("check_document_expiry failed: %s", e)

@shared_task
def check_ContractOrLeaveRequest_document_expiry():
    """Mark documents linked to Contract or LeaveRequest as expired if their end_date has passed."""
    try:
        today = timezone.localdate()
        # Get ContentType for Contract and LeaveRequest
        contract_ct = ContentType.objects.get_for_model(Contract)
        leave_request_ct = ContentType.objects.get_for_model(LeaveRequest)

        # Find valid documents linked to Contract or LeaveRequest
        expiring_docs = Document.objects.filter(
            status='valide',
            content_type__in=[contract_ct, leave_request_ct],
            object_id__isnull=False
        ).select_related('content_type')

        for doc in expiring_docs:
            try:
                # Get the associated object (Contract or LeaveRequest)
                related_object = doc.content_object
                if not related_object:
                    logger.warning(f"Document {doc.id} (type={doc.document_type}) has no valid related object")
                    continue

                # Check end_date based on the model
                end_date = None
                if isinstance(related_object, Contract):
                    end_date = related_object.end_date
                elif isinstance(related_object, LeaveRequest):
                    end_date = related_object.end_date

                # If end_date exists and is before today, mark document as expired
                if end_date and end_date < today:
                    doc.status = 'expiré'
                    doc.save(update_fields=['status'])
                    logger.debug(f"Marked document {doc.id} (type={doc.document_type}) as expiré for {related_object}")

            except Exception as e:
                logger.error(f"Error processing document {doc.id} (type={doc.document_type}): {e}")

    except Exception as e:
        logger.error(f"check_document_expiry failed: {e}")























