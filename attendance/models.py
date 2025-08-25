# attendance/models.py
from django.db import models
from .models_extra import *
from django.utils import timezone
import datetime

def today():
    return datetime.date.today()

class AttendanceRecord(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    date = models.DateField(default=today)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default='present', choices=[('present','Present'),('absent','Absent'), ('leave','Leave')])
    # For simplicity, status can be derived: if no check_in recorded by end of day, mark absent.

    class Meta:
        unique_together = ('employee', 'date')  # one record per employee per date

    def __str__(self):
        return f"{self.employee} - {self.date} : {self.status}"

