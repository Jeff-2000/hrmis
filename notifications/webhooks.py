# notifications/webhooks.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from .models import Notification
from django.conf import settings
from django.shortcuts import get_object_or_404
import json

# @csrf_exempt
# def twilio_status_webhook(request):
#     # Twilio posts form-encoded
#     sid = request.POST.get('MessageSid')
#     status = request.POST.get('MessageStatus')  # queued|sent|delivered|undelivered|failed|read?
#     q = Notification.objects.filter(provider='twilio', provider_message_id=sid)
#     if status in ('delivered','read'):
#         q.update(status=status, delivered_at=timezone.now())
#     elif status in ('failed','undelivered'):
#         q.update(status='failed')
#     elif status in ('sent','queued'):
#         q.update(status=status)
#     return HttpResponse(status=204)

# @csrf_exempt
# def whatsapp_cloud_webhook(request):
#     # Meta sends JSON with challenge on GET
#     if request.method == 'GET':
#         if request.GET.get('hub.verify_token') == getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', ''):
#             return HttpResponse(request.GET.get('hub.challenge'), status=200)
#         return HttpResponse(status=403)

#     try:
#         data = json.loads(request.body.decode('utf-8'))
#         # parse statuses
#         for entry in data.get('entry', []):
#             for change in entry.get('changes', []):
#                 value = change.get('value', {})
#                 for s in value.get('statuses', []):
#                     mid = s.get('id')
#                     st = s.get('status')  # sent, delivered, read, failed
#                     q = Notification.objects.filter(provider='whatsapp_cloud', provider_message_id=mid)
#                     if st == 'delivered':
#                         q.update(status='delivered', delivered_at=timezone.now())
#                     elif st == 'read':
#                         q.update(status='read', is_read=True, read_at=timezone.now())
#                     elif st in ('failed','undelivered'):
#                         q.update(status='failed')
#                     elif st == 'sent':
#                         q.update(status='sent')
#     except Exception:
#         pass
#     return HttpResponse(status=200)


# notifications/webhooks.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings
from .models import Notification
import json

# OPTIONAL: verify the webhook with Twilio signature
def _twilio_signature_valid(request) -> bool:
    try:
        if not getattr(settings, "TWILIO_VALIDATE_WEBHOOKS", False):
            return True
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        signature = request.headers.get("X-Twilio-Signature") or request.META.get("HTTP_X_TWILIO_SIGNATURE")
        # Raw URL without querystring for Django (typically request.build_absolute_uri())
        url = request.build_absolute_uri()
        # For POST form-encoded data, Twilio signs the POST fields
        form = request.POST.dict()
        return validator.validate(url, form, signature)
    except Exception:
        return False

@csrf_exempt
def twilio_status_webhook(request):
    # Twilio posts form-encoded for both SMS and WhatsApp
    if not _twilio_signature_valid(request):
        return HttpResponse(status=403)

    sid = request.POST.get("MessageSid") or request.POST.get("SmsSid")
    status = request.POST.get("MessageStatus") or request.POST.get("SmsStatus")  # queued|sent|delivered|undelivered|failed|read?
    error_code = request.POST.get("ErrorCode")  # may be empty
    # Match both SMS and WhatsApp providers sent via Twilio
    q = Notification.objects.filter(provider__in=["twilio", "twilio_whatsapp"], provider_message_id=sid)

    # Normalize and update
    if status in ("delivered", "read"):
        updates = {"status": status}
        if status == "delivered":
            updates["delivered_at"] = timezone.now()
        else:  # read
            updates["is_read"] = True
            updates["read_at"] = timezone.now()
        if error_code:
            # stash last error (if any) into metadata
            for n in q:
                m = n.metadata or {}
                m["twilio_error_code"] = error_code
                n.metadata = m
                n.save(update_fields=["status", "delivered_at", "is_read", "read_at", "metadata"] if status == "read"
                                   else ["status", "delivered_at", "metadata"])
        else:
            q.update(**updates)
    elif status in ("failed", "undelivered"):
        if error_code:
            for n in q:
                m = n.metadata or {}
                m["twilio_error_code"] = error_code
                n.metadata = m
                n.status = "failed"
                n.save(update_fields=["status", "metadata"])
        else:
            q.update(status="failed")
    elif status in ("sent", "queued"):
        q.update(status=status)

    return HttpResponse(status=204)


@csrf_exempt
def whatsapp_cloud_webhook(request):
    # Meta sends JSON with challenge on GET
    if request.method == "GET":
        if request.GET.get("hub.verify_token") == getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""):
            return HttpResponse(request.GET.get("hub.challenge"), status=200)
        return HttpResponse(status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
        # parse statuses
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for s in value.get("statuses", []):
                    mid = s.get("id")
                    st = s.get("status")  # sent, delivered, read, failed
                    q = Notification.objects.filter(provider="whatsapp_cloud", provider_message_id=mid)
                    if st == "delivered":
                        q.update(status="delivered", delivered_at=timezone.now())
                    elif st == "read":
                        q.update(status="read", is_read=True, read_at=timezone.now())
                    elif st in ("failed", "undelivered"):
                        q.update(status="failed")
                    elif st == "sent":
                        q.update(status="sent")
    except Exception:
        pass
    return HttpResponse(status=200)





