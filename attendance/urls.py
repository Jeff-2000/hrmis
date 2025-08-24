# attendance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'attendance', views.AttendanceRecordViewSet, basename='attendance')

urlpatterns = [
    path('attendance/dashboard/', views.attendance_dashboard_view, name='attendance_dashboard'),
    path('attendance/list/', views.attendance_list_view, name='attendance_list'),
    path('attendance/create/', views.attendance_create_view, name='attendance_create'),
    path('attendance/my/reccord/', views.my_attendance_view, name='my_attendance'),
    path('attendance/view/<int:pk>/', views.attendance_view_detail, name='attendance_view'),
    path('attendance/edit/<int:pk>/', views.attendance_edit_detail, name='attendance_edit'),
    path('attendance/delete/<int:pk>/', views.attendance_delete_detail, name='attendance_delete'),


    # path('api/v1/', include(router.urls)),
    path('', include(router.urls)),
]