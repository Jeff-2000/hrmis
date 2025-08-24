from main import views
from main.views import *
from django.urls import path
urlpatterns = [
    path('main/index/', views.main_view, name='main_view'),
    path('homeFake/', views.homeFakeView, name='homeFake_view'),
    path('main/home/', views.home_view, name='home_view'),
    
    # To test the main view
    path('main/profile/', views.profile_view, name='profile'),
    path('main/settings/', views.settings_view, name='settings'),
    path('main/help/', views.help_view, name='help'),
    path('main/fakebase/', views.fakebase_view, name='fakebase_view'),
]

# dashboard/urls.py
from django.urls import path
from .views import DashboardPageView, DashboardSummaryAPI
# Ensure the dashboard views are included in the main URL patterns
urlpatterns += [
    path("dashboard/", DashboardPageView.as_view(), name="home_dashboard"),
    path("dashboard/api/summary/", DashboardSummaryAPI.as_view(), name="summary"),
]

urlpatterns += [
    path("", views.public_home, name="public_home"),
    path("logout/", views.logout_view, name="logout"),
]

