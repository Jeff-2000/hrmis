# attendance/admin_extra.py
from django.contrib import admin
from .models_extra import AttendanceDevice, DeviceUserMapping


@admin.register(AttendanceDevice)
class AttendanceDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "vendor",
        "serial",
        "location",
        "timezone",
        "mode",
        "last_seen_at",
        "is_active",
    )
    list_filter = ("vendor", "mode", "is_active", "timezone")
    search_fields = ("serial", "location", "vendor")
    readonly_fields = ("last_seen_at",)


@admin.register(DeviceUserMapping)
class DeviceUserMappingAdmin(admin.ModelAdmin):
    list_display = ("device", "device_user_id", "employee")
    list_filter = ("device",)
    search_fields = ("device_user_id", "employee__first_name", "employee__last_name")
    autocomplete_fields = ("employee", "device")