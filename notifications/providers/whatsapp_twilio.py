# notifications/providers/whatsapp_twilio.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.conf import settings
from .base import ProviderResult
import logging
logger = logging.getLogger(__name__)

def _to_whatsapp_addr(e164: str) -> str:
    """
    Twilio WhatsApp requires 'whatsapp:+...' addressing.
    Pass in normalized E.164 (e.g. +225xxxxxxxxx) and we prefix it.
    """
    if not e164:
        raise ValueError("Missing destination phone (E.164).")
    return f"whatsapp:{e164}" if not e164.startswith("whatsapp:") else e164

def _from_whatsapp_addr() -> str:
    """
    Return your Twilio WhatsApp-enabled sender, like 'whatsapp:+14155238886'
    Configure TWILIO_WHATSAPP_FROM in settings.
    """
    sender = getattr(settings, "TWILIO_WHATSAPP_FROM", None)
    if not sender:
        raise RuntimeError("TWILIO_WHATSAPP_FROM is not configured.")
    return sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}"

def send_whatsapp_twilio(to_e164: str, message: str) -> ProviderResult:
    """
    Send a WhatsApp message via Twilio's WhatsApp channel.

    Requires:
      - settings.TWILIO_ACCOUNT_SID
      - settings.TWILIO_AUTH_TOKEN
      - settings.TWILIO_WHATSAPP_FROM (e.g. '+14155238886' or 'whatsapp:+14155238886')
    """
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are not configured.")

    client = Client(account_sid, auth_token)

    from_addr = _from_whatsapp_addr()
    to_addr = _to_whatsapp_addr(to_e164)

    try:
        msg = client.messages.create(
            from_=from_addr,
            to=to_addr,
            body=message,
        )
        logger.info("Twilio WA sent from=%s to=%s sid=%s status=%s", from_addr, to_addr, msg.sid, msg.status)
        
        # Twilio returns a Message instance with sid/status/etc.
        raw = {
            "sid": msg.sid,
            "status": msg.status,
            "num_segments": getattr(msg, "num_segments", None),
            "error_code": getattr(msg, "error_code", None),
            "error_message": getattr(msg, "error_message", None),
        }
        return ProviderResult(message_id=msg.sid, delivered=False, raw=raw)
    except TwilioRestException as e:
        # Surface Twilio error for upstream handling/fallback
        raise
