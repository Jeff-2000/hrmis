# feedback/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from .feedback_serializers import FeedbackCreateSerializer
from .tasks import send_feedback_alert

class SubmitFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # must be logged in

    @swagger_auto_schema(request_body=FeedbackCreateSerializer, responses={201: "Created"})
    def post(self, request):
        data = request.data.copy()
        # fallback page_url/user_agent from request if front-end didn't send
        data.setdefault("page_url", request.META.get("HTTP_REFERER", ""))
        data.setdefault("user_agent", request.META.get("HTTP_USER_AGENT", "")[:255])
        s = FeedbackCreateSerializer(data=data)
        s.is_valid(raise_exception=True)
        fb = s.save(user=request.user)
        # fire-and-forget alert
        send_feedback_alert.delay(fb.id)
        return Response({"ok": True, "id": fb.id}, status=status.HTTP_201_CREATED)
