# notifications/providers/whatsapp_cloud.py
import requests
from django.conf import settings
from .base import ProviderResult

# def send_whatsapp_cloud(to: str, message: str) -> ProviderResult:
#     url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
#     headers = {
#         'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',
#         'Content-Type': 'application/json'
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": to,
#         "type": "text",
#         "text": {"preview_url": False, "body": message}
#     }
#     r = requests.post(url, headers=headers, json=payload, timeout=15)
#     r.raise_for_status()
#     data = r.json()
#     mid = (data.get('messages') or [{}])[0].get('id', '')
#     return ProviderResult(message_id=mid, delivered=False, raw=data)


import requests
from django.conf import settings
from . base import ProviderResult
from requests.exceptions import HTTPError

def send_whatsapp_cloud(to: str, message: str) -> ProviderResult:
    url = f"https://graph.facebook.com/v23.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message}
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        mid = (data.get('messages') or [{}])[0].get('id', '')
        return ProviderResult(message_id=mid, delivered=False, raw=data)
    except HTTPError as e:
        if r.status_code == 401:
            # Log detailed error response for debugging
            error_data = r.json() if r.content else {'error': 'No response body'}
            raise HTTPError(f"401 Unauthorized: {error_data.get('error', {}).get('message', 'Unknown error')}")
        raise





