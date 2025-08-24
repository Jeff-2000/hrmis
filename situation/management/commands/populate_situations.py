from django.core.management.base import BaseCommand
from django.utils import timezone
from situation.models import Situation
from employee.models import Employee
from payroll.models import SituationType
from documents.models import Document
from datetime import timedelta
import uuid

class Command(BaseCommand):
    help = 'Populates the Situation model with sample data for testing'

    def handle(self, *args, **kwargs):
        # Replace these UUIDs with actual employee UUIDs from your database
        # Replace situation_type_id and document_id with actual IDs
        situations_data = [
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Replace with actual employee UUID
                'situation_type_id': 1,  # E.g., sick_leave
                'start_date': timezone.now().date() - timedelta(days=10),
                'end_date': timezone.now().date() + timedelta(days=5),
                'status': 'actif',
                'document_id': 1,  # Replace with actual document ID or set to None
                'availability_reason': 'Medical rest due to illness',
                'exclusion_reason': '',
                'exit_type': '',
            },
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Replace with actual employee UUID
                'situation_type_id': 2,  # E.g., training
                'start_date': timezone.now().date(),
                'end_date': None,
                'status': 'en attente',
                'document_id': None,
                'training_details': 'Leadership Training Program',
                'training_location': 'Paris',
                'availability_reason': '',
                'exclusion_reason': '',
                'exit_type': '',
            },
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Same employee as above
                'situation_type_id': 3,  # E.g., resignation
                'start_date': timezone.now().date() - timedelta(days=30),
                'end_date': timezone.now().date() - timedelta(days=1),
                'status': 'terminé',
                'document_id': 2,  # Replace with actual document ID or set to None
                'availability_reason': '',
                'exclusion_reason': '',
                'exit_type': 'resignation',
            },
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Replace with actual employee UUID
                'situation_type_id': 4,  # E.g., maternity_leave
                'start_date': timezone.now().date() - timedelta(days=20),
                'end_date': timezone.now().date() + timedelta(days=60),
                'status': 'actif',
                'document_id': None,
                'availability_reason': 'Maternity leave approved',
                'exclusion_reason': '',
                'exit_type': '',
            },
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Same employee as above
                'situation_type_id': 5,  # E.g., suspension
                'start_date': timezone.now().date() - timedelta(days=15),
                'end_date': timezone.now().date() - timedelta(days=5),
                'status': 'terminé',
                'document_id': 3,  # Replace with actual document ID or set to None
                'availability_reason': '',
                'exclusion_reason': 'Temporary suspension for investigation',
                'exit_type': '',
            },
        ]

        created_count = 0
        for data in situations_data:
            try:
                # Verify that referenced objects exist
                employee = Employee.objects.get(id=data['employee_id'])
                situation_type = SituationType.objects.get(id=data['situation_type_id'])
                document = Document.objects.get(id=data['document_id']) if data['document_id'] else None

                # Create or update situation
                situation, created = Situation.objects.update_or_create(
                    employee=employee,
                    situation_type=situation_type,
                    start_date=data['start_date'],
                    defaults={
                        'end_date': data.get('end_date'),
                        'status': data['status'],
                        'document': document,
                        'training_details': data.get('training_details', ''),
                        'training_location': data.get('training_location', ''),
                        'availability_reason': data.get('availability_reason', ''),
                        'exclusion_reason': data.get('exclusion_reason', ''),
                        'exit_type': data.get('exit_type', ''),
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created Situation: {situation.employee} - {situation.situation_type.name} "
                        f"({situation.start_date} to {situation.end_date or 'ongoing'})"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Updated Situation: {situation.employee} - {situation.situation_type.name} "
                        f"({situation.start_date} to {situation.end_date or 'ongoing'})"
                    ))
            except Employee.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Employee with ID {data['employee_id']} does not exist."
                ))
            except SituationType.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"SituationType with ID {data['situation_type_id']} does not exist."
                ))
            except Document.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Document with ID {data['document_id']} does not exist."
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error creating situation for employee ID {data['employee_id']}: {str(e)}"
                ))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} situations."))