from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet

# Register API ViewSet routes
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/delete/<uuid:id>/', views.employee_delete_view, name='employee_delete'),
    path('employees/edit/<uuid:id>/', views.employee_edit_view, name='employee_edit'),
    path('employees/<uuid:id>/', views.employee_detail_view, name='employee_detail'),
    # path('employees/create/', views.employee_create_form_view, name='employee_create'),
    # path('employees/create/submit/', views.employee_create_view, name='employee_create_submit'),
]


urlpatterns += [
    # Existing URLs
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/delete/<uuid:id>/', views.employee_delete_view, name='employee_delete'),
    path('employees/edit/<uuid:id>/', views.employee_edit_view, name='employee_edit'),
    path('employees/<uuid:id>/', views.employee_detail_view, name='employee_detail'),
    
    # New URLs for create views
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/departments/create/', views.department_create_view, name='department_create'),
    
    # Grade routes
    path('employees/grades/create/', views.grade_create_view, name='grade_create'),
    path('employees/grades/', views.grade_list_api, name='grade_list_api'),  # GET for list, POST handled by grade_create_view
    path('employees/grades/list/', views.grade_list_view, name='grade_list'),  # For UI listing
    path('employees/grades/view/<int:id>/', views.grade_detail_view, name='grade_detail'),
    path('employees/grades/edit/<int:id>/', views.grade_edit_view, name='grade_edit'),  # PATCH for edit
    path('employees/grades/delete/<int:id>/', views.grade_delete_view, name='grade_delete'),  # DELETE for delete
    
    
    
    # Department routes
    path('employees/departments/list/', views.department_list_view, name='department_list'),
    path('employees/departments/', views.department_list_api, name='department_list_api'),
    path('employees/departments/create/', views.department_create_view, name='department_create'),
    path('employees/departments/view/<int:id>/', views.department_detail_view, name='department_detail'),
    path('employees/departments/edit/<int:id>/', views.department_edit_view, name='department_edit'),  # PATCH for edit
    path('employees/departments/delete/<int:id>/', views.department_delete_view, name='department_delete'),  # DELETE for delet
    path('employees/departments/choices/', views.department_choices_api, name='department_choices_api'),  # For parent selection in forms
    
    # API endpoint for employee creation (already implied in employee_create_view)
    path('api/v1/employees/', views.employee_create_view, name='employee_create_api'),
]

# Add ViewSet routes (API)
urlpatterns += router.urls