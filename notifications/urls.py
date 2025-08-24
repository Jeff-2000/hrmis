# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import NotificationViewSet, NotificationPreferenceViewSet, notification_center_view

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'preferences', NotificationPreferenceViewSet, basename='preferences')

urlpatterns = [
    path('notifications/', include(router.urls)),
    path('notifications/center/', notification_center_view, name='notification_center'),
]

# notifications/urls.py (add)
from . webhooks import twilio_status_webhook, whatsapp_cloud_webhook

urlpatterns += [
    path('webhooks/twilio/', twilio_status_webhook, name='notify_twilio_webhook'),
    path('webhooks/whatsapp/', whatsapp_cloud_webhook, name='notify_whatsapp_webhook'),
]
