# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import F
from django.conf import settings
from .models import Notification, NotificationPreference
from authentication.models import User
from .providers.sms_twilio import send_sms_twilio
from .providers.whatsapp_cloud import send_whatsapp_cloud
import logging
logger = logging.getLogger(__name__)

# @shared_task
# def send_notification(user_id, message, channel=None):
#     """Send a notification to a user via their preferred channel."""
#     try:
#         user = User.objects.get(id=user_id)
#         # Get user's preferred notification channel
#         preference = NotificationPreference.objects.filter(
#             user=user, is_active=True
#         ).order_by('channel').first()

#         if not preference:
#             logger.warning(f"No active notification preference for user {user.username}")
#             channel = channel or 'EMAIL'
#             contact = user.email or user.employee.contact
#         else:
#             channel = channel or preference.channel
#             contact = preference.contact

#         if not contact:
#             raise ValueError(f"No contact information available for user {user.username}")

#         # Simulate sending notification (replace with actual integration)
#         logger.info(f"Sending {channel} to {contact}: {message}")
#         notification = Notification.objects.create(
#             user=user,
#             channel=channel.upper(),
#             recipient=contact,
#             message=message,
#             status='sent'
#         )

#         # Example integration (uncomment and configure as needed)
#         """
#         if channel == 'EMAIL':
#             send_mail(
#                 subject='HRMIS Notification',
#                 message=message,
#                 from_email='no-reply@hrmis.com',
#                 recipient_list=[contact],
#                 fail_silently=False
#             )
#         elif channel in ['SMS', 'WHATSAPP']:
#             # Integrate with Twilio or similar service
#             pass
#         """

#         return True
#     except Exception as e:
#         logger.error(f"Failed to send {channel} to {user_id}: {str(e)}")
#         Notification.objects.create(
#             user=user,
#             channel=channel.upper() if channel else 'UNKNOWN',
#             recipient=contact or 'unknown',
#             message=message,
#             status='failed'
#         )
#         return False



# notifications/tasks.py
from celery import shared_task
import logging
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone

from .models import Notification, NotificationPreference
from authentication.models import User

logger = logging.getLogger(__name__)

def _extract_provider_ids_and_raw(res):
    """
    Accepts various provider return shapes and extracts a message id and raw dict.
    Supported:
      - Twilio Message instance (has .sid)
      - Objects with .message_id/.sid and maybe .to_dict()
      - Dict-like payloads
      - None
    """
    message_id = ""
    raw = {}

    if res is None:
        return message_id, raw

    # Twilio: MessageInstance has .sid and .__dict__ includes a lot; keep it light
    if hasattr(res, "sid"):
        message_id = getattr(res, "sid", "") or ""
        try:
            # twilio objects often support .__dict__ with private attrs; avoid dumping internals
            raw = {"sid": message_id}
        except Exception:
            pass
        return message_id, raw

    # Generic: .message_id
    if hasattr(res, "message_id"):
        message_id = getattr(res, "message_id", "") or ""
    # Try to_dict
    if hasattr(res, "to_dict"):
        try:
            raw = res.to_dict() or {}
        except Exception:
            raw = {}
    # Fallback: mapping/dict-like
    if isinstance(res, dict):
        raw = res
        message_id = raw.get("message_id") or raw.get("sid") or message_id

    return message_id, raw



# @shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
# def send_notification(self, user_id, message, channel=None, title="", category="", recipient_override=None, priority=None, metadata=None):
#     """
#         Send a notification using the user's active preference (or the forced 'channel').
#         Backwards compatible — new keyword-only args are optional.

#         Arguments
#         ---------
#         user_id: int
#         message: str
#         channel: Optional[str]  -> 'EMAIL' | 'SMS' | 'WHATSAPP' | 'INAPP'
#         title: str
#         category: str
#         recipient_override: Optional[str]  -> email or phone to bypass preference routing
#         priority: Optional[int]            -> 1 (High) ... 5 (Low), if omitted, model default is used
#         metadata: Optional[dict]           -> extra context (e.g. {'deeplink': '/leaves/requests/12'})
#     """
    
#     user = User.objects.filter(id=user_id).first()
#     if not user:
#         logger.warning("send_notification: user %s not found", user_id); return False

#     # preference
#     pref = NotificationPreference.objects.filter(user=user, is_active=True).first()
#     chosen_channel = (channel or (pref.channel if pref else 'EMAIL')).upper()

#     # destination
#     contact = recipient_override
#     if not contact:
#         if chosen_channel == 'EMAIL':
#             contact = user.email or getattr(getattr(user, 'employee', None), 'contact', None)
#         else:
#             contact = getattr(getattr(user, 'employee', None), 'contact', None)
#     if not contact:
#         logger.error("No contact for user %s", user); return False

#     # create record first
#     n = Notification.objects.create(
#         user=user, channel=chosen_channel, recipient=contact, title=title, message=message,
#         category=category, status='queued', priority=priority=, metadata=metadata or {},
#     )

#     try:
#         n.status = 'sending'; n.save(update_fields=['status'])

#         if chosen_channel == 'SMS':
#             res = send_sms_twilio(contact, message)
#             n.provider = 'twilio'
#         elif chosen_channel == 'WHATSAPP':
#             res = send_whatsapp_cloud(contact, message)
#             n.provider = 'whatsapp_cloud'
#         elif chosen_channel == 'EMAIL':
#             # your email adapter here (or Django send_mail)
#             from django.core.mail import send_mail
#             send_mail(title or 'Notification', message, None, [contact], fail_silently=False)
#             res = None
#             n.provider = 'email'
#         else:
#             # INAPP or others → just mark sent
#             res = None
#             n.provider = chosen_channel.lower()

#         n.status = 'sent'
#         if res:
#             n.provider_message_id = res.message_id
#             n.metadata = {**(n.metadata or {}), **(res.raw or {})}
#         n.save(update_fields=['status','provider','provider_message_id','metadata'])
#         return True

#     except Exception as e:
#         logger.exception("send_notification failed: %s", e)
#         n.status = 'failed'
#         n.retry_count = F('retry_count') + 1
#         n.metadata = {**(n.metadata or {}), 'error': str(e)}
#         n.save(update_fields=['status','retry_count','metadata'])
#         raise  # let Celery retry with backoff



# @shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
# def send_notification(
#         self,
#         user_id,
#         message,
#         channel=None,
#         title="",
#         category="",
#         recipient_override=None,
#         priority=None,
#         metadata=None,
#     ):
    
#     """
#         Send a notification using the user's active preference (or the forced 'channel').
#         Backwards compatible — new keyword-only args are optional.

#         Arguments
#         ---------
#         user_id: int
#         message: str
#         channel: Optional[str]  -> 'EMAIL' | 'SMS' | 'WHATSAPP' | 'INAPP'
#         title: str
#         category: str
#         recipient_override: Optional[str]  -> email or phone to bypass preference routing
#         priority: Optional[int]            -> 1 (High) ... 5 (Low), if omitted, model default is used
#         metadata: Optional[dict]           -> extra context (e.g. {'deeplink': '/leaves/requests/12'})
#     """
    
#     user = User.objects.filter(id=user_id).first()
#     if not user:
#         logger.warning("send_notification: user %s not found", user_id)
#         return False

#     # preference
#     pref = NotificationPreference.objects.filter(user=user, is_active=True).first()
#     chosen_channel = (channel or (pref.channel if pref else 'EMAIL')).upper()

#     # destination
#     contact = recipient_override
#     if not contact:
#         if chosen_channel == 'EMAIL':
#             contact = user.email or getattr(getattr(user, 'employee', None), 'contact', None)
#         else:
#             contact = getattr(getattr(user, 'employee', None), 'contact', None)
#     if not contact:
#         logger.error("No contact for user %s", user)
#         return False

#     # create record first
#     n = Notification.objects.create(
#         user=user,
#         channel=chosen_channel,
#         recipient=contact,
#         title=title,
#         message=message,
#         category=category,
#         status="queued",
#         priority=priority,
#         metadata=metadata or {},
#     )

#     try:
#         n.status = "sending"
#         n.save(update_fields=["status"])

#         # send
#         if chosen_channel == "SMS":
#             res = send_sms_twilio(contact, message)
#             n.provider = "twilio"
#         elif chosen_channel == "WHATSAPP":
#             res = send_whatsapp_cloud(contact, message)
#             n.provider = "whatsapp_cloud"
#         elif chosen_channel == "EMAIL":
#             from django.core.mail import send_mail

#             send_mail(title or "Notification", message, None, [contact], fail_silently=False)
#             res = None
#             n.provider = "email"
#         else:
#             # INAPP or others → no external send
#             res = None
#             n.provider = chosen_channel.lower()

#         # normalize provider response
#         message_id, raw = _extract_provider_ids_and_raw(res)
#         n.status = "sent"
#         n.provider_message_id = message_id
#         n.metadata = {**(n.metadata or {}), **raw}

#         n.save(update_fields=["status", "provider", "provider_message_id", "metadata"])
#         return True

#     except Exception as e:
#         logger.exception("send_notification failed: %s", e)
#         n.status = "failed"
#         n.retry_count = F("retry_count") + 1
#         n.metadata = {**(n.metadata or {}), "error": str(e)}
#         n.save(update_fields=["status", "retry_count", "metadata"])
#         raise

# @shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
# def send_notification(
#     self,
#     user_id,
#     message,
#     channel=None,
#     title="",
#     category="",
#     recipient_override=None,
#     priority=None,
#     metadata=None,
# ):
#     """
#     Send a notification using the user's active preference (or the forced 'channel').
#     Backwards compatible — new keyword-only args are optional.

#     Arguments
#     ---------
#     user_id: int
#     message: str
#     channel: Optional[str]  -> 'EMAIL' | 'SMS' | 'WHATSAPP' | 'INAPP'
#     title: str
#     category: str
#     recipient_override: Optional[str]  -> email or phone to bypass preference routing
#     priority: Optional[int]            -> 1 (High) ... 5 (Low), defaults to 3 if None
#     metadata: Optional[dict]           -> extra context (e.g. {'deeplink': '/leaves/requests/12'})
#     """
#     user = User.objects.filter(id=user_id).first()
#     if not user:
#         logger.warning("send_notification: user %s not found", user_id)
#         return False

#     # Use model default (3) if priority is None or invalid
#     effective_priority = priority if isinstance(priority, int) and 1 <= priority <= 5 else 3

#     # Preference
#     pref = NotificationPreference.objects.filter(user=user, is_active=True).first()
#     chosen_channel = (channel or (pref.channel if pref else 'EMAIL')).upper()

#     # Destination
#     contact = recipient_override
#     if not contact:
#         if chosen_channel == 'EMAIL':
#             contact = user.email or getattr(getattr(user, 'employee', None), 'contact', None)
#         else:
#             contact = getattr(getattr(user, 'employee', None), 'contact', None)
#     if not contact:
#         logger.error("No contact for user %s", user)
#         return False

#     # Create record
#     n = Notification.objects.create(
#         user=user,
#         channel=chosen_channel,
#         recipient=contact,
#         title=title,
#         message=message,
#         category=category,
#         status="queued",
#         priority=effective_priority,  # Use effective_priority instead of priority
#         metadata=metadata or {},
#     )

#     try:
#         n.status = "sending"
#         n.save(update_fields=["status"])

#         # Send
#         if chosen_channel == "SMS":
#             res = send_sms_twilio(contact, message)
#             n.provider = "twilio"
#         elif chosen_channel == "WHATSAPP":
#             res = send_whatsapp_cloud(contact, message)
#             n.provider = "whatsapp_cloud"
#         elif chosen_channel == "EMAIL":
#             from django.core.mail import send_mail
#             send_mail(title or "Notification", message, None, [contact], fail_silently=False)
#             res = None
#             n.provider = "email"
#         else:
#             # INAPP or others → no external send
#             res = None
#             n.provider = chosen_channel.lower()

#         # Normalize provider response
#         message_id, raw = _extract_provider_ids_and_raw(res)
#         n.status = "sent"
#         n.provider_message_id = message_id
#         n.metadata = {**(n.metadata or {}), **raw}

#         n.save(update_fields=["status", "provider", "provider_message_id", "metadata"])
#         return True

#     except Exception as e:
#         logger.exception("send_notification failed: %s", e)
#         n.status = "failed"
#         n.retry_count = F("retry_count") + 1
#         n.metadata = {**(n.metadata or {}), "error": str(e)}
#         n.save(update_fields=["status", "retry_count", "metadata"])
#         raise


import re
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from twilio.base.exceptions import TwilioRestException
from authentication.models import User
from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

# def _extract_provider_ids_and_raw(res):
#     # Placeholder for extracting provider message IDs (unchanged)
#     message_id = getattr(res, 'sid', '') if res else ''
#     raw = {'response': str(res)} if res else {}
#     return message_id, raw

# def is_valid_email(email):
#     """Check if the input string is a valid email address."""
#     if not email:
#         return False
#     # Basic email regex validation
#     email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
#     return bool(re.match(email_pattern, email.strip()))

# def normalize_phone_number(phone):
#     if not phone:
#         return None
#     # Remove everything except digits
#     cleaned = re.sub(r'\D', '', phone.strip())
    
#     # Ensure it starts with country code 225
#     if cleaned.startswith('225'):
#         cleaned = f'+{cleaned}'
#     elif cleaned.startswith('0'):
#         # Replace leading 0 with 225
#         cleaned = '+225' + cleaned[1:]
#     else:
#         # Assume local number missing country code
#         cleaned = '+225' + cleaned

#     # Validate length (WhatsApp accepts 12-15 digits with +)
#     if not re.match(r'^\+\d{10,14}$', cleaned):
#         return None

#     return cleaned

# @shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
# def send_notification(
#     self,
#     user_id,
#     message,
#     channel=None,
#     title="",
#     category="",
#     recipient_override=None,
#     priority=None,
#     metadata=None,
# ):
#     """
#     Send a notification using the user's active preference (or the forced 'channel').
#     Validates if contact is a phone number or email and falls back to user.email if needed.

#     Arguments
#     ---------
#     user_id: int
#     message: str
#     channel: Optional[str]  -> 'EMAIL' | 'SMS' | 'WHATSAPP' | 'INAPP'
#     title: str
#     category: str
#     recipient_override: Optional[str]  -> email or phone to bypass preference routing
#     priority: Optional[int]  -> 1 (High) ... 5 (Low), defaults to 3 if None
#     metadata: Optional[dict]  -> extra context (e.g. {'deeplink': '/leaves/requests/12'})
#     """
#     user = User.objects.filter(id=user_id).first()
#     if not user:
#         logger.warning("send_notification: user %s not found", user_id)
#         return False

#     # Use model default (3) if priority is None or invalid
#     effective_priority = priority if isinstance(priority, int) and 1 <= priority <= 5 else 3

#     # Preference
#     pref = NotificationPreference.objects.filter(user=user, is_active=True).first()
#     chosen_channel = (channel or (pref.channel if pref else 'EMAIL')).upper()

#     # Destination
#     contact = recipient_override
#     if not contact:
#         contact = getattr(getattr(user, 'employee', None), 'contact', None)
#         if contact:
#             if chosen_channel in ('SMS', 'WHATSAPP'):
#                 # Check if contact is a valid phone number
#                 contact = normalize_phone_number(contact)
#                 if not contact:
#                     # Not a valid phone number, try email
#                     contact = user.email if is_valid_email(user.email) else None
#                     chosen_channel = 'EMAIL' if contact else 'INAPP'
#             elif chosen_channel == 'EMAIL':
#                 # Check if contact is a valid email
#                 if not is_valid_email(contact):
#                     contact = user.email if is_valid_email(user.email) else None
#                     chosen_channel = 'INAPP' if not contact else 'EMAIL'
#         else:
#             # No contact, use user.email for EMAIL or fall back to INAPP
#             contact = user.email if is_valid_email(user.email) else None
#             chosen_channel = 'EMAIL' if contact and chosen_channel == 'EMAIL' else 'INAPP'

#     if not contact:
#         logger.error("No valid contact for user %s (channel: %s), using INAPP", user_id, chosen_channel)
#         chosen_channel = 'INAPP'
#         contact = f"user_{user_id}@no-contact.example.com"

#     # Create record
#     n = Notification.objects.create(
#         user=user,
#         channel=chosen_channel,
#         recipient=contact,
#         title=title,
#         message=message,
#         category=category,
#         status="queued",
#         priority=effective_priority,
#         metadata=metadata or {},
#     )

#     try:
#         n.status = "sending"
#         n.save(update_fields=["status"])

#         # Send
#         if chosen_channel == "SMS":
#             try:
#                 from .providers.sms_twilio import send_sms_twilio
#                 res = send_sms_twilio(contact, message)
#                 n.provider = "twilio"
#             except TwilioRestException as e:
#                 if e.code == 21211:  # Invalid phone number
#                     logger.error("Invalid phone number %s for user %s", contact, user_id)
#                     n.status = "failed"
#                     n.metadata = {**(n.metadata or {}), "error": f"Invalid phone number: {str(e)}"}
#                     n.save(update_fields=["status", "metadata"])
#                     return False
#                 raise  # Retry other Twilio errors
#         elif chosen_channel == "WHATSAPP":
#             from .providers.whatsapp_cloud import send_whatsapp_cloud
#             res = send_whatsapp_cloud(contact, message)
#             n.provider = "whatsapp_cloud"
#         elif chosen_channel == "EMAIL":
#             send_mail(title or "Notification", message, None, [contact], fail_silently=False)
#             res = None
#             n.provider = "email"
#         else:
#             # INAPP or others → no external send
#             res = None
#             n.provider = chosen_channel.lower()

#         # Normalize provider response
#         message_id, raw = _extract_provider_ids_and_raw(res)
#         n.status = "sent"
#         n.provider_message_id = message_id
#         n.metadata = {**(n.metadata or {}), **raw}

#         n.save(update_fields=["status", "provider", "provider_message_id", "metadata"])
#         return True

#     except Exception as e:
#         logger.exception("send_notification failed: %s", e)
#         n.status = "failed"
#         n.retry_count = F("retry_count") + 1
#         n.metadata = {**(n.metadata or {}), "error": str(e)}
#         n.save(update_fields=["status", "retry_count", "metadata"])
#         raise

import re
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from twilio.base.exceptions import TwilioRestException
from requests.exceptions import HTTPError
from authentication.models import User
from .models import Notification, NotificationPreference
from .providers.sms_twilio import send_sms_twilio
from .providers.whatsapp_cloud import send_whatsapp_cloud

logger = logging.getLogger(__name__)


def is_valid_email(email):
    if not email:
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))

# # def normalize_phone_number(phone):
# #     if not phone:
# #         return None
# #     cleaned = re.sub(r'[^\d+]', '', phone.strip())
# #     if not cleaned.startswith('+'):
# #         cleaned = f'+225{cleaned}'
# #     if not re.match(r'^\+\d{10,14}$', cleaned):
# #         return None
# #     return cleaned

def normalize_phone_number(phone):
    if not phone:
        return None
    # Remove everything except digits
    cleaned = re.sub(r'\D', '', phone.strip())
    
    # Ensure it starts with country code 225
    if cleaned.startswith('225'):
        cleaned = f'+{cleaned}'
    elif cleaned.startswith('0'):
        # Replace leading 0 with 225
        cleaned = '+225' + cleaned[1:]
    else:
        # Assume local number missing country code
        cleaned = '+225' + cleaned

    # Validate length (WhatsApp accepts 12-15 digits with +)
    if not re.match(r'^\+\d{10,14}$', cleaned):
        return None

    return cleaned

@shared_task(bind=True, max_retries=5, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def send_notification(
    self,
    user_id,
    message,
    channel=None,
    title="",
    category="",
    recipient_override=None,
    priority=None,
    metadata=None,
):
    user = User.objects.filter(id=user_id).first()
    if not user:
        logger.warning("send_notification: user %s not found", user_id)
        return False

    effective_priority = priority if isinstance(priority, int) and 1 <= priority <= 5 else 3
    pref = NotificationPreference.objects.filter(user=user, is_active=True).first()
    chosen_channel = (channel or (pref.channel if pref else 'EMAIL')).upper()

    contact = recipient_override
    if not contact:
        contact = getattr(getattr(user, 'employee', None), 'contact', None)
        if contact:
            if chosen_channel in ('SMS', 'WHATSAPP'):
                contact = normalize_phone_number(contact)
                if not contact:
                    contact = user.email if is_valid_email(user.email) else None
                    chosen_channel = 'EMAIL' if contact else 'INAPP'
            elif chosen_channel == 'EMAIL':
                if not is_valid_email(contact):
                    contact = user.email if is_valid_email(user.email) else None
                    chosen_channel = 'INAPP' if not contact else 'EMAIL'
        else:
            contact = user.email if is_valid_email(user.email) else None
            chosen_channel = 'EMAIL' if contact and chosen_channel == 'EMAIL' else 'INAPP'

    if not contact:
        logger.error("No valid contact for user %s (channel: %s), using INAPP", user_id, chosen_channel)
        chosen_channel = 'INAPP'
        contact = f"user_{user_id}@no-contact.example.com"

    n = Notification.objects.create(
        user=user,
        channel=chosen_channel,
        recipient=contact,
        title=title,
        message=message,
        category=category,
        status="queued",
        priority=effective_priority,
        metadata=metadata or {},
    )

    try:
        n.status = "sending"
        n.save(update_fields=["status"])

        if chosen_channel == "SMS":
            try:
                res = send_sms_twilio(contact, message)
                n.provider = "twilio"
            except TwilioRestException as e:
                if e.code == 21211:
                    logger.error("Invalid phone number %s for user %s", contact, user_id)
                    n.status = "failed"
                    n.metadata = {**(n.metadata or {}), "error": f"Invalid phone number: {str(e)}"}
                    n.save(update_fields=["status", "metadata"])
                    return False
                raise
        # # Without fallbact to twilio whatsapp: using only META whatsapp
        # elif chosen_channel == "WHATSAPP":
        #     try:
        #         res = send_whatsapp_cloud(contact, message)
        #         n.provider = "whatsapp_cloud"
        #     except HTTPError as e:
        #         if e.response.status_code == 401:
        #             logger.error("WhatsApp authentication failed for user %s: %s", user_id, str(e))
        #             n.status = "failed"
        #             n.metadata = {**(n.metadata or {}), "error": f"WhatsApp auth error: {str(e)}"}
        #             n.save(update_fields=["status", "metadata"])
        #             # Fall back to EMAIL or INAPP
        #             if is_valid_email(user.email):
        #                 chosen_channel = "EMAIL"
        #                 contact = user.email
        #                 send_mail(title or "Notification", message, None, [contact], fail_silently=False)
        #                 n.channel = "EMAIL"
        #                 n.recipient = contact
        #                 n.status = "sent"
        #                 n.provider = "email"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True
        #             else:
        #                 n.channel = "INAPP"
        #                 n.recipient = f"user_{user_id}@no-contact.example.com"
        #                 n.status = "sent"
        #                 n.provider = "inapp"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True
        #         raise

        # With fallbact to twilio whatsapp
        elif chosen_channel == "WHATSAPP":
            logger.info("WA send attempt (cloud) user=%s to=%s", user_id, contact)
            try:
                # 1) Try Meta WhatsApp Cloud first
                res = send_whatsapp_cloud(contact, message)
                n.provider = "whatsapp_cloud"
                logger.info("WA cloud ok user=%s mid=%s", user_id, getattr(res, 'message_id', None))

            except HTTPError as e:
                # If Cloud auth or API error -> try Twilio WhatsApp as fallback
                try:
                    from .providers.whatsapp_twilio import send_whatsapp_twilio
                    logger.warning("WA cloud failed (%s). Falling back to Twilio WA. user=%s to=%s", getattr(e.response, 'status_code', None), user_id, contact)
                    twilio_res = send_whatsapp_twilio(contact, message)
                    res = twilio_res
                    n.provider = "twilio_whatsapp"   # distinguish from SMS 'twilio'
                    logger.info("Twilio WA ok user=%s sid=%s", user_id, getattr(res, 'message_id', None))
                    
                except TwilioRestException as tw_e:
                    # Hard fail after both providers rejected
                    n.status = "failed"
                    n.metadata = {
                        **(n.metadata or {}),
                        "error": f"WA Cloud+Twilio failed: cloud={str(e)}, twilio={str(tw_e)}",
                    }
                    n.save(update_fields=["status", "metadata"])
                    # Optional: EMAIL/INAPP last-chance fallback
                    if is_valid_email(user.email):
                        chosen_channel = "EMAIL"
                        contact = user.email
                        send_mail(title or "Notification", message, None, [contact], fail_silently=False)
                        n.channel = "EMAIL"
                        n.recipient = contact
                        n.status = "sent"
                        n.provider = "email"
                        n.save(update_fields=["channel", "recipient", "status", "provider"])
                        return True
                    else:
                        n.channel = "INAPP"
                        n.recipient = f"user_{user_id}@no-contact.example.com"
                        n.status = "sent"
                        n.provider = "inapp"
                        n.save(update_fields=["channel", "recipient", "status", "provider"])
                        return True

            except Exception as e:
                # Unknown Cloud error -> try Twilio as best-effort fallback too
                try:
                    from .providers.whatsapp_twilio import send_whatsapp_twilio
                    twilio_res = send_whatsapp_twilio(contact, message)
                    res = twilio_res
                    n.provider = "twilio_whatsapp"
                except Exception as tw_e:
                    raise  # Let outer handler capture and mark failed

        # # With fallbact to META whatsapp
        # elif chosen_channel == "WHATSAPP":
        #     logger.info("WA send attempt (twilio-first) user=%s to=%s", user_id, contact)
        #     try:
        #         # 1) Try Twilio WhatsApp first
        #         from .providers.whatsapp_twilio import send_whatsapp_twilio
        #         twilio_res = send_whatsapp_twilio(contact, message)
        #         res = twilio_res
        #         n.provider = "twilio_whatsapp"   # distinct from SMS 'twilio'
        #         logger.info("Twilio WA ok user=%s sid=%s", user_id, getattr(res, 'message_id', None))

        #     except TwilioRestException as tw_e:
        #         # If it's an invalid number, Cloud will almost certainly fail too — short-circuit.
        #         if getattr(tw_e, "code", None) == 21211:
        #             logger.error("Twilio WA invalid phone %s for user %s (21211). Skipping Cloud fallback.", contact, user_id)
        #             n.status = "failed"
        #             n.metadata = {**(n.metadata or {}), "error": f"Twilio WA invalid phone: {str(tw_e)}"}
        #             n.save(update_fields=["status", "metadata"])

        #             # Optional last-chance fallback: EMAIL or INAPP
        #             if is_valid_email(user.email):
        #                 chosen_channel = "EMAIL"
        #                 contact = user.email
        #                 send_mail(title or "Notification", message, None, [contact], fail_silently=False)
        #                 n.channel = "EMAIL"
        #                 n.recipient = contact
        #                 n.status = "sent"
        #                 n.provider = "email"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True
        #             else:
        #                 n.channel = "INAPP"
        #                 n.recipient = f"user_{user_id}@no-contact.example.com"
        #                 n.status = "sent"
        #                 n.provider = "inapp"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True

        #         # Otherwise, fall back to WhatsApp Cloud
        #         logger.warning(
        #             "Twilio WA failed (code=%s). Falling back to WA Cloud. user=%s to=%s",
        #             getattr(tw_e, "code", None), user_id, contact
        #         )
        #         try:
        #             res = send_whatsapp_cloud(contact, message)
        #             n.provider = "whatsapp_cloud"
        #             logger.info("WA Cloud ok user=%s mid=%s", user_id, getattr(res, 'message_id', None))
        #         except HTTPError as cloud_e:
        #             # Both providers failed -> EMAIL/INAPP fallback
        #             n.status = "failed"
        #             n.metadata = {
        #                 **(n.metadata or {}),
        #                 "error": f"Twilio WA+Cloud failed: twilio={str(tw_e)}, cloud={str(cloud_e)}",
        #             }
        #             n.save(update_fields=["status", "metadata"])

        #             if is_valid_email(user.email):
        #                 chosen_channel = "EMAIL"
        #                 contact = user.email
        #                 send_mail(title or "Notification", message, None, [contact], fail_silently=False)
        #                 n.channel = "EMAIL"
        #                 n.recipient = contact
        #                 n.status = "sent"
        #                 n.provider = "email"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True
        #             else:
        #                 n.channel = "INAPP"
        #                 n.recipient = f"user_{user_id}@no-contact.example.com"
        #                 n.status = "sent"
        #                 n.provider = "inapp"
        #                 n.save(update_fields=["channel", "recipient", "status", "provider"])
        #                 return True

        #     except Exception as tw_unknown:
        #         # Unknown Twilio error -> try Cloud as best-effort
        #         logger.warning("Twilio WA unexpected error: %s; trying WA Cloud. user=%s", tw_unknown, user_id)
        #         try:
        #             res = send_whatsapp_cloud(contact, message)
        #             n.provider = "whatsapp_cloud"
        #             logger.info("WA Cloud ok user=%s mid=%s", user_id, getattr(res, 'message_id', None))
        #         except Exception as cloud_unknown:
        #             # Let outer handler record failure & retry policy
        #             raise

        elif chosen_channel == "EMAIL":
            send_mail(title or "Notification", message, None, [contact], fail_silently=False)
            res = None
            n.provider = "email"
        else:
            res = None
            n.provider = chosen_channel.lower()

        message_id, raw = _extract_provider_ids_and_raw(res)
        n.status = "sent"
        n.provider_message_id = message_id
        n.metadata = {**(n.metadata or {}), **raw}
        n.save(update_fields=["status", "provider", "provider_message_id", "metadata"])
        return True

    except Exception as e:
        logger.exception("send_notification failed: %s", e)
        n.status = "failed"
        n.retry_count = F("retry_count") + 1
        n.metadata = {**(n.metadata or {}), "error": str(e)}
        n.save(update_fields=["status", "retry_count", "metadata"])
        raise

