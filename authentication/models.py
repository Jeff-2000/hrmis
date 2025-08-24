# authentication/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('HR', 'HR Officer'),
        ('MANAGER', 'Manager'),
        ('EMP', 'Employee'),
        ('AUDITOR', 'Auditor'),
    ]
    role = models.CharField(max_length=7, choices=ROLE_CHOICES, default='EMP')
    # Link to Employee profile (optional, if every user corresponds to an employee record)
    employee_profile = models.OneToOneField(
        'employee.Employee',
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='linked_user',
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
