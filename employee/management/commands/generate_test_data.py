from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from employee.models import Department, Grade, Employee
from faker import Faker
import uuid
from random import choice, randint

class Command(BaseCommand):
    help = 'Generate test data for Department, Grade, and Employee models'

    def handle(self, *args, **options):
        # Initialize Faker with French locale for Ivorian context
        fake = Faker('fr_FR')

        # Clear existing data (optional, comment out to append)
        Department.objects.all().delete()
        Grade.objects.all().delete()
        Employee.objects.all().delete()
        User = get_user_model()
        # User.objects.all().delete()  # Clear users to avoid conflicts

        # Create Departments
        departments_data = [
            {"name": "Ministère de l'Éducation Nationale", "parent": None},
            {"name": "Ministère de la Santé Publique", "parent": None},
            {"name": "Ministère des Finances", "parent": None},
            {"name": "Direction des Ressources Humaines", "parent": "Ministère de l'Éducation Nationale"},
            {"name": "Service de Formation", "parent": "Direction des Ressources Humaines"},
            {"name": "Direction des Hôpitaux", "parent": "Ministère de la Santé Publique"},
            {"name": "Service de Gestion Budgétaire", "parent": "Ministère des Finances"},
            {"name": "Ministère de l'Agriculture", "parent": None},
            {"name": "Direction des Projets Agricoles", "parent": "Ministère de l'Agriculture"},
            {"name": "Service de Logistique", "parent": "Ministère de l'Éducation Nationale"},
        ]

        departments = {}
        for dept_data in departments_data:
            parent_name = dept_data["parent"]
            parent = departments.get(parent_name) if parent_name else None
            dept = Department.objects.create(name=dept_data["name"], parent=parent)
            departments[dept_data["name"]] = dept

        # Create Grades
        grades_data = [
            {"code": "A1", "description": "Administrateur Principal"},
            {"code": "A2", "description": "Administrateur"},
            {"code": "B1", "description": "Technicien Supérieur"},
            {"code": "B2", "description": "Technicien"},
            {"code": "C1", "description": "Agent Administratif Principal"},
            {"code": "C2", "description": "Agent Administratif"},
            {"code": "D1", "description": "Assistant Administratif"},
            {"code": "D2", "description": "Agent d'Exécution"},
        ]

        grades = {}
        for grade_data in grades_data:
            grade = Grade.objects.create(code=grade_data["code"], description=grade_data["description"])
            grades[grade_data["code"]] = grade

        # Create Employees
        ivorian_names = {
            "male": [
                ("Koffi", "Yao"), ("Kouassi", "N'Guessan"), ("Jean", "Kouadio"), ("Amadou", "Traoré"),
                ("Moussa", "Diarrassouba"), ("Adama", "Koné"), ("Sébastien", "Bamba"), ("Franck", "Ouattara"),
            ],
            "female": [
                ("Aminata", "Coulibaly"), ("Fatou", "Diaby"), ("Marie", "Kouamé"), ("Awa", "Traoré"),
                ("Rose", "Yao"), ("Élodie", "N'Guessan"), ("Sophie", "Koné"), ("Clarisse", "Bamba"),
            ]
        }

        regions = ["Abidjan", "Yamoussoukro", "Bouaké", "Daloa", "San-Pédro", "Korhogo"]
        employment_types = ["Fonctionnaire", "Agent contractuel"]
        qualification_categories = ["A", "B", "C", "D"]
        current_classes = ["1ère classe", "2ème classe", "3ème classe"]

        for i in range(20):
            gender = choice(["M", "F"])
            names = ivorian_names["male" if gender == "M" else "female"]
            first_name, last_name = choice(names)
            
            # Generate unique username
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}.{counter}"
                counter += 1
            
            # Generate random dates
            dob = fake.date_of_birth(minimum_age=22, maximum_age=60)
            date_joined = fake.date_between(start_date="-20y", end_date="today")
            
            # Create user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@fonctionpublique.ci",
                    password="Test1234!",
                    role=choice(['ADMIN', 'HR', 'EMP'])
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating user {username}: {e}"))
                continue
            
            # Create employee
            Employee.objects.create(
                id=uuid.uuid4(),
                user=user,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                nationality="Ivoirienne",
                contact=f"+225 {fake.phone_number()[:10]}",
                employment_type=choice(employment_types),
                grade=choice(list(grades.values())),
                department=choice(list(departments.values())),
                position=fake.job(),
                date_joined=date_joined,
                status=choice(["actif", "inactif"]),
                origin_structure=choice(["Ministère de l'Éducation", "Ministère de la Santé", "Structure Privée"]),
                workplace=choice(["Abidjan", "Yamoussoukro", "Bouaké"]),
                region=choice(regions),
                qualification_category=choice(qualification_categories),
                current_class=choice(current_classes),
                echelon=randint(1, 10)
            )

        self.stdout.write(self.style.SUCCESS('Test data generated successfully!'))
        self.stdout.write(self.style.SUCCESS(
            f'Created {Department.objects.count()} departments, '
            f'{Grade.objects.count()} grades, {Employee.objects.count()} employees, '
            f'{User.objects.count()} users.'
        ))