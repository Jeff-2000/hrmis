# situation/models.py
from django.db import models
from django.utils import timezone
from payroll.models import SituationType

class Situation(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    situation_type = models.ForeignKey('payroll.SituationType', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        default='actif', 
        choices=[('actif', 'Actif'), ('terminé', 'Terminé'), ('en attente', 'En attente')]
    )
    document = models.ForeignKey('documents.Document', null=True, blank=True, on_delete=models.SET_NULL)
    tranche_1_start = models.DateField(null=True, blank=True)
    tranche_1_end = models.DateField(null=True, blank=True)
    tranche_2_start = models.DateField(null=True, blank=True)
    tranche_2_end = models.DateField(null=True, blank=True)
    tranche_3_start = models.DateField(null=True, blank=True)
    tranche_3_end = models.DateField(null=True, blank=True)
    training_details = models.CharField(max_length=100, blank=True)
    training_location = models.CharField(max_length=50, blank=True)
    physical_control = models.BooleanField(null=True, blank=True)
    resumption_date = models.DateField(null=True, blank=True)
    detachment_duration = models.CharField(max_length=20, blank=True)
    availability_reason = models.CharField(max_length=100, blank=True)
    exclusion_reason = models.CharField(max_length=100, blank=True)
    exit_type = models.CharField(max_length=50, blank=True)

    def is_active(self):
        today = timezone.now().date()
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today

    def __str__(self):
        return f"{self.employee} - {self.situation_type.name} ({self.start_date} to {self.end_date or 'ongoing'})"
    
    class Meta:
        ordering = ['-start_date']