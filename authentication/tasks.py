# feedback/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from .feedback_models import Feedback
from notifications.tasks import send_notification  
from config.monitoring.metrics import mark_beat_run
import logging
logger = logging.getLogger(__name__)

FEEDBACK_CATEGORY = "feedback"

@shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def send_feedback_alert(self, feedback_id: int):
    """
    Notify all admins (role='ADMIN') and staff (is_staff=True) when feedback arrives.
    """
    
    # Mark task as run in monitorinG
    mark_beat_run("feedback.tasks.send_feedback_alert")
    
    try:
        fb = Feedback.objects.select_related("user").get(id=feedback_id)
    except Feedback.DoesNotExist:
        logger.warning("Feedback %s not found", feedback_id)
        return False

    title = "Nouveau feedback utilisateur"
    who = f"{getattr(fb.user, 'username', 'Utilisateur')}"
    msg = (
        f"{who} a soumis un feedback ({fb.rating}/5) le {timezone.localtime(fb.created_at).strftime('%d/%m/%Y %H:%M')}.\n"
        f"Page: {fb.page_url or '—'}\n"
        f"Commentaire: {fb.comment or '—'}"
    )
    meta = {"feedback_id": fb.id, "rating": fb.rating, "page_url": fb.page_url}

    User = get_user_model()
    recipients = list(User.objects.filter(is_staff=True))  # staff=True includes admins
    try:
        # If you have role field:
        admin_qs = User.objects.filter(role="ADMIN")
        recipients_ids = {u.id for u in recipients}
        recipients += [u for u in admin_qs if u.id not in recipients_ids]
    except Exception:
        pass  # role may not exist; ignore

    for u in recipients:
        # let your notification chooser pick channel based on prefs
        send_notification.delay(
            user_id=u.id,
            title=title,
            message=msg,
            category=FEEDBACK_CATEGORY,
            priority=3,
            metadata=meta,
        )
    return True
