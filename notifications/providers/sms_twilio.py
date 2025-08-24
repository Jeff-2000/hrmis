# notifications/providers/sms_twilio.py
from twilio.rest import Client
from django.conf import settings
from .base import ProviderResult

def send_sms_twilio(to: str, message: str) -> ProviderResult:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        to=to, from_=settings.TWILIO_FROM, body=message,
        status_callback=getattr(settings, 'NOTIFY_TWILIO_CALLBACK', None)
    )
    return ProviderResult(message_id=msg.sid, delivered=False, raw={'sid': msg.sid})
