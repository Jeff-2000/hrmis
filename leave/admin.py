# leave/admin.py

from django.contrib import admin
from .models import LeaveType, LeaveBalance, Holiday, Delegation, LeaveRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'accrual_rate_per_month', 'max_per_year', 'carry_over_limit', 'requires_attachment', 'is_hourly')
    search_fields = ('name', 'code')
    list_filter = ('requires_attachment', 'is_hourly')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'balance')
    search_fields = ('employee__first_name', 'employee__last_name', 'leave_type__name')
    list_filter = ('year', 'leave_type')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'region')
    search_fields = ('name', 'region')
    list_filter = ('region',)


@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    list_display = ('delegator', 'delegate', 'start_date', 'end_date', 'is_active')
    search_fields = ('delegator__username', 'delegate__username')
    list_filter = ('start_date', 'end_date')

    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = "Active?"


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'leave_type', 'start_date', 'end_date', 'status',
        'approved_by', 'requested_at', 'is_half_day', 'is_read'
    )
    search_fields = (
        'employee__first_name', 'employee__last_name',
        'leave_type__name', 'approved_by__username'
    )
    list_filter = ('status', 'leave_type', 'is_half_day', 'requested_at')
    readonly_fields = ('requested_at',)