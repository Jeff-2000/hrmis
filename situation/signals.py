from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Situation
from django.utils import timezone

@receiver(post_save, sender=Situation)
def update_employee_status(sender, instance, **kwargs):
    employee = instance.employee
    code = instance.situation_type.code.lower()
    today = timezone.now().date()

    if code in ['resignation', 'death', 'retirement', 'exit']:
        employee.is_active = False
        employee.save()
    elif code == 'suspension' and instance.end_date and instance.end_date <= today:
        employee.is_active = True
        employee.save()