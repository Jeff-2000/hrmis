from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth', 'nationality', 'contact',
            'employment_type', 'grade', 'department', 'position', 'date_joined', 'status',
            'origin_structure', 'workplace', 'region', 'qualification_category', 'current_class', 'echelon'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
        }