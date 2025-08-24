from django.urls import path
from . import views  # or the correct module if your views are elsewhere
from django.contrib.auth.views import LoginView, LogoutView


from django.views.generic import TemplateView # For static templates like dashboard

# Import your authentication views if custom, or use Django's built-in
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('index/', views.index_view, name='index'),
    # Add other URL patterns as needed
]



urlpatterns += [

    # --- UI Routes ---
    path('', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), # Redirects to login after logout
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # ... include other password reset URLs as needed ...


    # Admin Specific UI views
    path('admin-users/', TemplateView.as_view(template_name='admin/user_management.html'), name='user-management'),

    path('notification-settings/', TemplateView.as_view(template_name='admin/notification_settings.html'), name='notification-settings'),

    # Add other paths as you create specific UI templates for each section
]




from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render

urlpatterns += [
    # Placeholder URLs for sidebar navigation (to be implemented as needed)
    path('', lambda request: render(request, 'main/home.html'), name='home'),
    path('profile/', lambda request: render(request, 'main/profile.html'), name='profile'),
    path('help/', lambda request: render(request, 'main/help.html'), name='help'),
    path('admin/users/', lambda request: render(request, 'main/user_management.html'), name='user_management'),
    path('admin/notifications/settings/', lambda request: render(request, 'notifications/notification_settings.html'), name='notification_settings'),
]


from django.urls import path
from .views import login_view, logout_view

urlpatterns += [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]