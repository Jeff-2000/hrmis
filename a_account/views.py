# a_account/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import UserSetting
from .serializers import UserSettingSerializer

# Pages
class ProfilePage(LoginRequiredMixin, TemplateView):
    template_name = "a_account/profile.html"

class NotificationSettingsPage(LoginRequiredMixin, TemplateView):
    template_name = "a_account/notification_settings.html"

class GeneralSettingsPage(LoginRequiredMixin, TemplateView):
    template_name = "a_account/settings.html"

class HelpPage(TemplateView):  # public
    template_name = "a_account/help.html"


# API
class UserSettingViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_or_create(self, user):
        obj, _ = UserSetting.objects.get_or_create(user=user)
        return obj

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        obj = self._get_or_create(request.user)
        if request.method.lower() == "get":
            return Response(UserSettingSerializer(obj).data)

        ser = UserSettingSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_200_OK)




