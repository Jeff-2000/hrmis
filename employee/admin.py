# employee/admin.py
from django.contrib import admin
from .models import *

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'grade', 'department', 'position', 'status')
    list_filter = ('gender', 'department', 'grade', 'status', 'region', 'qualification_category')
    search_fields = ('last_name', 'first_name', 'contact', 'position')
    autocomplete_fields = ['grade', 'department', 'user']
    
