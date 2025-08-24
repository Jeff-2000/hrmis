# leave/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveTypeViewSet, LeaveBalanceViewSet
from . import views

router = DefaultRouter()
router.register(r'leave', LeaveRequestViewSet, basename='leave')
router.register(r'leave-types', LeaveTypeViewSet, basename='leave-types')
router.register(r'leave-balances', LeaveBalanceViewSet, basename='leave-balances')

urlpatterns = [
    path('leave/', include(router.urls)),  # Include router-generated URLs
    path('leave/create/', views.leave_create_view, name='leave_create'),  # Define this view for the create form
    path('leave/list/', views.leave_list_view, name='leave_list'),  # Assuming you have a view for listing leaves
    path('leave/management/', views.leave_management_view, name='leave_management'),
    path('leave/my_leave/', views.my_leave_view, name='my_leave'),
    path('leave/my_create/', views.my_leave_create_view, name='my_leave_create'),
    path('leave/calendar/', views.leave_calendar_view, name='leave_calendar'),
]










