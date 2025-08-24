from django.db import models
# models_extra.py (optional helpers) for biometric attendance devices
class AttendanceDevice(models.Model):
    vendor = models.CharField(max_length=50, blank=True)
    serial = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default="Africa/Abidjan")
    mode = models.CharField(max_length=16, choices=[("PUSH","Push"),("PULL","Pull")], default="PUSH")
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

class DeviceUserMapping(models.Model):
    device = models.ForeignKey(AttendanceDevice, on_delete=models.CASCADE)
    device_user_id = models.CharField(max_length=64)
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    class Meta:
        unique_together = ("device","device_user_id")
