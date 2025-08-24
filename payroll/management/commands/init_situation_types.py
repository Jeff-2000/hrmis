from django.core.management.base import BaseCommand
from payroll.models import SituationType

class Command(BaseCommand):
    help = 'Initialize SituationType records'

    def handle(self, *args, **kwargs):
        situation_types = [
            ('Congé de maladie', 'sick_leave', False),
            ('Training/Formation', 'training', False),
            ('Détachement', 'detachment', True),
            ('Disponibilité', 'availability', True),
            ('Exclusion Temporaire', 'exclusion', True),
            ('Démission', 'resignation', True),
            ('Retraite', 'retirement', True),
            ('Décès', 'death', True),
            ('Congé de maternité', 'maternity_leave', False),
            ('Congé parental', 'parental_leave', False),
            ('Suspension', 'suspension', True),
            ('Sortie de carrière', 'exit', True),
        ]

        for name, code, suspend_payroll in situation_types:
            SituationType.objects.get_or_create(
                name=name,
                code=code,
                defaults={'suspend_payroll': suspend_payroll}
            )
        self.stdout.write(self.style.SUCCESS('Successfully initialized SituationType records'))