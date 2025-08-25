# employee/models.py
import uuid
from django.db import models
from django.core.exceptions import ValidationError
import re

class Department(models.Model):
    """Organizational unit (e.g., ministry department or structure)."""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    # Additional fields like code, etc., can be added for hierarchy
    def __str__(self):
        return self.name

class Grade(models.Model):
    """Civil service grade or rank, e.g., A1, B2, etc."""
    code = models.CharField(max_length=10, unique=True)  # e.g. "A1"
    description = models.CharField(max_length=100, blank=True)
    # Perhaps salary scale or level can be included
    def __str__(self):
        return self.code

# class Employee(models.Model):
#     """Employee (civil servant) profile. Uses UUID as primary key."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Unique ID:contentReference[oaicite:9]{index=9}
#     user = models.OneToOneField('authentication.User', null=True, blank=True, on_delete=models.SET_NULL,
#                                 related_name='employee')  # link to auth user, if exists
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     gender = models.CharField(max_length=1, choices=[('M','M'),('F','F')])
#     date_of_birth = models.DateField(null=True, blank=True)
#     nationality = models.CharField(max_length=50, default="Ivorian")
#     contact = models.CharField(max_length=100, blank=True)  # could store phone/email
#     employment_type = models.CharField(max_length=50, verbose_name="Type d'emploi", 
#                                        help_text="e.g. Fonctionnaire or Agent contractuel")
#     grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
#     department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
#                                    related_name='employees',
#                                    help_text="Current department or structure")
#     position = models.CharField(max_length=100, blank=True, help_text="Job title or position")
#     date_joined = models.DateField(null=True, blank=True, help_text="Date of entry into service")
#     status = models.CharField(max_length=20, default="actif", help_text="Employment status (actif/inactif)")
#     # Other fields capturing the structure:
#     origin_structure = models.CharField(max_length=100, blank=True, help_text="Original structure of appointment")
#     workplace = models.CharField(max_length=100, blank=True, help_text="Current workplace location")
#     region = models.CharField(max_length=50, blank=True, help_text="Region of assignment")
#     # Qualification category (A, B, C, D) and class (e.g., 1st class, 2nd class)
#     qualification_category = models.CharField(max_length=1, blank=True, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
#     current_class = models.CharField(max_length=20, blank=True, help_text="e.g. 1ère classe, 2ème classe")
#     echelon = models.PositiveIntegerField(null=True, blank=True, help_text="Current echelon level")
#     manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subordinates')

#     def clean(self):
#         if self.manager and self.manager == self:
#             raise ValidationError("An employee cannot be their own manager.")

#     def __str__(self):
#         return f"{self.user.get_full_name()}"

#     @property
#     def is_manager(self):
#         return self.subordinates.exists()
    
#     def __str__(self):
#         return f"{self.last_name} {self.first_name} (Grade {self.grade})"



def normalize_phone_number(phone):
    if not phone:
        return None
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    if not cleaned.startswith('+'):
        cleaned = f'+225{cleaned}'
    if not re.match(r'^\+\d{10,14}$', cleaned):
        return None
    return cleaned

def is_valid_email(email):
    if not email:
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))

class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('authentication.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='employee')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=[('M','M'),('F','F')])
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, default="Ivorian")
    contact = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(max_length=50, verbose_name="Type d'emploi", help_text="e.g. Fonctionnaire or Agent contractuel")
    grade = models.ForeignKey('Grade', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', help_text="Current department or structure")
    position = models.CharField(max_length=100, blank=True, help_text="Job title or position")
    date_joined = models.DateField(null=True, blank=True, help_text="Date of entry into service")
    status = models.CharField(max_length=20, default="actif", help_text="Employment status (actif/inactif)")
    origin_structure = models.CharField(max_length=100, blank=True, help_text="Original structure of appointment")
    workplace = models.CharField(max_length=100, blank=True, help_text="Current workplace location")
    region = models.CharField(max_length=50, blank=True, help_text="Region of assignment")
    qualification_category = models.CharField(max_length=1, blank=True, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    current_class = models.CharField(max_length=20, blank=True, help_text="e.g. 1ère classe, 2ème classe")
    echelon = models.PositiveIntegerField(null=True, blank=True, help_text="Current echelon level")
    manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subordinates')
    primary_worksite = models.ForeignKey('Worksite', null=True, blank=True,
                                         on_delete=models.SET_NULL, related_name='employees')

    def clean(self):
        if self.manager and self.manager == self:
            raise ValidationError("An employee cannot be their own manager.")
        if self.contact:
            if not (normalize_phone_number(self.contact) or is_valid_email(self.contact)):
                raise ValidationError(f"Invalid contact: {self.contact}. Must be a valid phone number (e.g., +22512345678) or email.")

    def save(self, *args, **kwargs):
        if self.contact:
            # Normalize phone number if valid
            phone = normalize_phone_number(self.contact)
            if phone:
                self.contact = phone
            # Otherwise, assume it's an email and validate
            elif not is_valid_email(self.contact):
                raise ValidationError(f"Invalid contact: {self.contact}. Must be a valid phone number or email.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name} (Grade {self.grade})"

    @property
    def is_manager(self):
        return self.subordinates.exists()
    
    @property
    def region_obj(self):
        return self.primary_worksite.region if self.primary_worksite else None

    @property
    def region_name(self):
        return self.region_obj.name if self.region_obj else None


class Region(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)       # e.g., 'ABJ', 'YM', etc.
    name = models.CharField(max_length=120, unique=True)      # e.g., 'Abidjan', 'Yamoussoukro'
    quota = models.PositiveIntegerField(default=0)            # headcount quota target (optional)
    active = models.BooleanField(default=True)

    # (Optional) simple geo centroid for mapping; keep if you don't use PostGIS… yet
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["name"])]

    def __str__(self):
        return f"{self.code} — {self.name}"

class Worksite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey('employee.Department', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='worksites')
    address = models.CharField(max_length=255, blank=True)

    # ⬇️ Replace old text field with a proper FK
    region = models.ForeignKey(Region, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='worksites')

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    allowed_radius_m = models.PositiveIntegerField(default=150)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["code"])]

    def __str__(self):
        return f"{self.code} - {self.name}"






