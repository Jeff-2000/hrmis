
# a_account/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProfilePage, NotificationSettingsPage, GeneralSettingsPage, HelpPage,
    UserSettingViewSet
)

router = DefaultRouter()
router.register("a_account/settings", UserSettingViewSet, basename="user-settings")

urlpatterns = [
    path("profile/", ProfilePage.as_view(), name="profile"),
    path("settings/notifications/", NotificationSettingsPage.as_view(), name="notification_settings"),
    path("settings/", GeneralSettingsPage.as_view(), name="general_settings"),
    path("help/", HelpPage.as_view(), name="help"),
]
urlpatterns += router.urls

