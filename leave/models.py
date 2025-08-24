# leave/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from authentication.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from datetime import timedelta

class LeaveType(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    accrual_rate_per_month = models.DecimalField(max_digits=5, decimal_places=2)  # e.g. 1.66 days
    max_per_year = models.DecimalField(max_digits=5, decimal_places=2)
    carry_over_limit = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    requires_attachment = models.BooleanField(default=False)
    is_hourly = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    balance = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.date})"

class Delegation(models.Model):
    delegator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegations_given')
    delegate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegations_received')
    start_date = models.DateField()
    end_date = models.DateField()

    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

class LeaveRequest(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'En attente'),
        ('manager_approved', 'Approuvé par manager'),
        ('hr_approved', 'Approuvé par HR'),
        ('rejected', 'Rejeté'),
        ('taken', 'Pris')
    ])
    approved_by = models.ForeignKey('authentication.User', null=True, blank=True, on_delete=models.SET_NULL)
    requested_at = models.DateTimeField(default=now)
    document = models.ForeignKey('documents.Document', null=True, blank=True, on_delete=models.SET_NULL)
    rejection_reason = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)

    def calculate_working_days(self):
        if self.is_half_day:
            return 0.5
        delta = self.end_date - self.start_date
        days = delta.days + 1
        # Exclude weekends (simplified)
        start = self.start_date
        working_days = 0
        for i in range(days):
            current_day = start + timedelta(days=i)
            if current_day.weekday() < 5:  # Monday to Friday
                working_days += 1
        return working_days

    @property
    def calculate_working_days_property(self):
        return self.calculate_working_days()

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['start_date','status']),   # NEW
            models.Index(fields=['requested_at']),          # helpful for SLA/aging
        ]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"





