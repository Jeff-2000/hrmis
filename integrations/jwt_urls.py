# integrations/jwt_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Give this module an app_name distinct from its parent
app_name = "integrations_jwt"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair_jwt"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh_jwt"),
]
