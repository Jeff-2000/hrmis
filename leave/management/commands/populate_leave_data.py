from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from leave.models import LeaveType, LeaveBalance, Delegation, LeaveRequest
from employee.models import Employee, Grade, Department
from payroll.models import Contract
from documents.models import Document
from django.contrib.contenttypes.models import ContentType
import decimal
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate sample data for Grade, Department, Employee, Contract, LeaveType, LeaveBalance, Delegation, and LeaveRequest models'

    def handle(self, *args, **kwargs):
        # Create Grades
        try:
            grade_a1 = Grade.objects.get_or_create(
                code='A1',
                defaults={'description': 'Senior Civil Service Grade'}
            )[0]
            grade_b2 = Grade.objects.get_or_create(
                code='B2',
                defaults={'description': 'Mid-level Civil Service Grade'}
            )[0]
            self.stdout.write(self.style.SUCCESS('Created grades'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating grades: {e}'))
            return

        # Create Departments
        try:
            dept_finance = Department.objects.get_or_create(
                name='Finance',
                defaults={'parent': None}
            )[0]
            dept_hr = Department.objects.get_or_create(
                name='Human Resources',
                defaults={'parent': None}
            )[0]
            self.stdout.write(self.style.SUCCESS('Created departments'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating departments: {e}'))
            return

        # Create Users
        try:
            manager = User.objects.get_or_create(
                username='manager1',
                defaults={
                    'email': 'manager1@example.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'role': 'MANAGER'
                }
            )[0]
            hr = User.objects.get_or_create(
                username='hr1',
                defaults={
                    'email': 'hr1@example.com',
                    'first_name': 'HR',
                    'last_name': 'Admin',
                    'role': 'HR'
                }
            )[0]
            employee1 = User.objects.get_or_create(
                username='emp1',
                defaults={
                    'email': 'emp1@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'role': 'EMPLOYEE'
                }
            )[0]
            employee2 = User.objects.get_or_create(
                username='emp2',
                defaults={
                    'email': 'emp2@example.com',
                    'first_name': 'Alice',
                    'last_name': 'Johnson',
                    'role': 'EMPLOYEE'
                }
            )[0]
            self.stdout.write(self.style.SUCCESS('Created users'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating users: {e}'))
            return

        # Create Employees
        try:
            emp1 = Employee.objects.get_or_create(
                user=employee1,
                defaults={
                    'id': uuid.uuid4(),
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'gender': 'M',
                    'date_of_birth': date(1985, 5, 15),
                    'nationality': 'Ivorian',
                    'contact': 'john.doe@example.com',
                    'employment_type': 'Fonctionnaire',
                    'grade': grade_a1,
                    'department': dept_finance,
                    'position': 'Accountant',
                    'date_joined': date(2015, 1, 1),
                    'status': 'actif',
                    'origin_structure': 'Ministry of Finance',
                    'workplace': 'Abidjan',
                    'region': 'Lagunes',
                    'qualification_category': 'A',
                    'current_class': '1ère classe',
                    'echelon': 3
                }
            )[0]
            emp2 = Employee.objects.get_or_create(
                user=employee2,
                defaults={
                    'id': uuid.uuid4(),
                    'first_name': 'Alice',
                    'last_name': 'Johnson',
                    'gender': 'F',
                    'date_of_birth': date(1990, 8, 20),
                    'nationality': 'Ivorian',
                    'contact': 'alice.johnson@example.com',
                    'employment_type': 'Agent contractuel',
                    'grade': grade_b2,
                    'department': dept_hr,
                    'position': 'HR Assistant',
                    'date_joined': date(2018, 3, 1),
                    'status': 'actif',
                    'origin_structure': 'Ministry of Labor',
                    'workplace': 'Yamoussoukro',
                    'region': 'Lacs',
                    'qualification_category': 'B',
                    'current_class': '2ème classe',
                    'echelon': 2
                }
            )[0]
            self.stdout.write(self.style.SUCCESS('Created employees'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating employees: {e}'))
            return

        # Create Contracts
        try:
            Contract.objects.get_or_create(
                employee=emp1,
                contract_type='PERMANENT',
                salary=decimal.Decimal('500000.00'),
                start_date=date(2015, 1, 1),
                defaults={
                    'status': 'ACTIVE',
                    'notes': 'Initial permanent contract'
                }
            )
            Contract.objects.get_or_create(
                employee=emp2,
                contract_type='CONTRACTUAL',
                salary=decimal.Decimal('400000.00'),
                start_date=date(2018, 3, 1),
                defaults={
                    'status': 'ACTIVE',
                    'notes': 'Initial contract'
                }
            )
            self.stdout.write(self.style.SUCCESS('Created contracts'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating contracts: {e}'))
            return

        # Create Leave Types
        try:
            annual = LeaveType.objects.get_or_create(
                name='Annual Leave',
                code='ANN',
                defaults={
                    'description': 'Annual vacation leave',
                    'accrual_rate_per_month': decimal.Decimal('1.67'),
                    'max_per_year': decimal.Decimal('20.00'),
                    'carry_over_limit': decimal.Decimal('10.00'),
                    'requires_attachment': False,
                    'is_hourly': False
                }
            )[0]
            sick = LeaveType.objects.get_or_create(
                name='Sick Leave',
                code='SICK',
                defaults={
                    'description': 'Leave for medical reasons',
                    'accrual_rate_per_month': decimal.Decimal('1.00'),
                    'max_per_year': decimal.Decimal('12.00'),
                    'carry_over_limit': decimal.Decimal('0.00'),
                    'requires_attachment': True,
                    'is_hourly': False
                }
            )[0]
            personal = LeaveType.objects.get_or_create(
                name='Personal Leave',
                code='PERS',
                defaults={
                    'description': 'Leave for personal matters',
                    'accrual_rate_per_month': decimal.Decimal('0.50'),
                    'max_per_year': decimal.Decimal('6.00'),
                    'carry_over_limit': decimal.Decimal('0.00'),
                    'requires_attachment': False,
                    'is_hourly': True
                }
            )[0]
            self.stdout.write(self.style.SUCCESS('Created leave types'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating leave types: {e}'))
            return

        # Create Leave Balances
        try:
            LeaveBalance.objects.get_or_create(
                employee=emp1,
                leave_type=annual,
                year=2025,
                defaults={'balance': decimal.Decimal('20.00')}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp1,
                leave_type=sick,
                year=2025,
                defaults={'balance': decimal.Decimal('12.00')}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp1,
                leave_type=personal,
                year=2025,
                defaults={'balance': decimal.Decimal('6.00')}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp2,
                leave_type=annual,
                year=2025,
                defaults={'balance': decimal.Decimal('20.00')}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp2,
                leave_type=sick,
                year=2025,
                defaults={'balance': decimal.Decimal('12.00')}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp2,
                leave_type=personal,
                year=2025,
                defaults={'balance': decimal.Decimal('6.00')}
            )
            self.stdout.write(self.style.SUCCESS('Created leave balances'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating leave balances: {e}'))
            return

        # Create Delegations
        try:
            Delegation.objects.get_or_create(
                delegator=manager,
                delegate=hr,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 15),
                defaults={}
            )
            Delegation.objects.get_or_create(
                delegator=employee1,
                delegate=manager,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 7),
                defaults={}
            )
            Delegation.objects.get_or_create(
                delegator=employee2,
                delegate=manager,
                start_date=date(2025, 10, 1),
                end_date=date(2025, 10, 10),
                defaults={}
            )
            Delegation.objects.get_or_create(
                delegator=manager,
                delegate=employee1,
                start_date=date(2025, 11, 1),
                end_date=date(2025, 11, 5),
                defaults={}
            )
            self.stdout.write(self.style.SUCCESS('Created delegations'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating delegations: {e}'))
            return

        # Create Leave Requests and Associated Documents
        try:
            content_type = ContentType.objects.get_for_model(LeaveRequest)
            today = timezone.now().date()

            # Leave Request 1: John - Annual, no document
            lr1 = LeaveRequest.objects.get_or_create(
                employee=emp1,
                leave_type=annual,
                start_date=today,
                end_date=today + timedelta(days=5),
                defaults={
                    'is_half_day': False,
                    'reason': 'Family vacation',
                    'status': 'pending',
                    'requested_at': timezone.now()
                }
            )[0]

            # Leave Request 2: John - Sick, with document
            lr2 = LeaveRequest.objects.get_or_create(
                employee=emp1,
                leave_type=sick,
                start_date=date(2025, 8, 10),
                end_date=date(2025, 8, 12),
                defaults={
                    'is_half_day': False,
                    'reason': 'Medical procedure',
                    'status': 'manager_approved',
                    'approved_by': manager,
                    'requested_at': timezone.now() - timedelta(days=10)
                }
            )[0]
            Document.objects.get_or_create(
                content_type=content_type,
                object_id=lr2.id,
                document_type='certificat_medical',
                issuance_date=date(2025, 8, 1),
                defaults={
                    'issued_by': 'Dr. Smith',
                    'file': 'documents/medical_certificate_001.pdf',
                    'content_text': 'Medical certificate for surgery',
                    'status': 'valide'
                }
            )

            # Leave Request 3: Alice - Sick, with document
            lr3 = LeaveRequest.objects.get_or_create(
                employee=emp2,
                leave_type=sick,
                start_date=date(2025, 8, 15),
                end_date=date(2025, 8, 16),
                defaults={
                    'is_half_day': False,
                    'reason': 'Flu recovery',
                    'status': 'hr_approved',
                    'approved_by': hr,
                    'requested_at': timezone.now() - timedelta(days=5)
                }
            )[0]
            Document.objects.get_or_create(
                content_type=content_type,
                object_id=lr3.id,
                document_type='certificat_medical',
                issuance_date=date(2025, 8, 10),
                defaults={
                    'issued_by': 'Dr. Jones',
                    'file': 'documents/medical_certificate_002.pdf',
                    'content_text': 'Medical certificate for flu treatment',
                    'status': 'valide'
                }
            )

            # Leave Request 4: Alice - Personal, no document
            LeaveRequest.objects.get_or_create(
                employee=emp2,
                leave_type=personal,
                start_date=date(2025, 8, 20),
                end_date=date(2025, 8, 20),
                defaults={
                    'is_half_day': True,
                    'start_time': time(9, 0),
                    'end_time': time(13, 0),
                    'duration_hours': decimal.Decimal('4.00'),
                    'reason': 'Personal appointment',
                    'status': 'pending',
                    'requested_at': timezone.now()
                }
            )

            # Leave Request 5: John - Annual, rejected, no document
            LeaveRequest.objects.get_or_create(
                employee=emp1,
                leave_type=annual,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 7),
                defaults={
                    'is_half_day': False,
                    'reason': 'Extended holiday',
                    'status': 'rejected',
                    'approved_by': manager,
                    'requested_at': timezone.now() - timedelta(days=15)
                }
            )
            self.stdout.write(self.style.SUCCESS('Created leave requests and documents'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating leave requests and documents: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Successfully populated all sample data'))