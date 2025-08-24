# employee/serializers.py
from rest_framework import serializers
from .models import *
from authentication.models import User

# serializers.py
class DepartmentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'employee_count']

    # Optional: for list/detail, if you want to show more info about the parent
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Replace parent id by dict with id and name (for frontend display)
        parent_obj = instance.parent
        data['parent'] = {"id": parent_obj.id, "name": parent_obj.name} if parent_obj else None
        return data
    
    def get_employee_count(self, obj):
        return obj.employees.count()
    
class GradeSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Grade
        fields = ['id', 'code', 'description', 'employee_count']

class EmployeeSerializer(serializers.ModelSerializer):
    grade = GradeSerializer(read_only=True)
    grade_id = serializers.PrimaryKeyRelatedField(source='grade', queryset=Grade.objects.all(), write_only=True, allow_null=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(source='department', queryset=Department.objects.all(), write_only=True, allow_null=True)
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    gender = serializers.ChoiceField(choices=[('M', 'M'), ('F', 'F')], required=True)
    employment_type = serializers.CharField(required=True, allow_blank=False)
    nationality = serializers.CharField(required=True, allow_blank=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'first_name', 'last_name', 'gender', 'date_of_birth', 'nationality', 'contact',
            'employment_type', 'grade', 'grade_id', 'department', 'department_id', 'position',
            'date_joined', 'status', 'origin_structure', 'workplace', 'region',
            'qualification_category', 'current_class', 'echelon'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Convert empty strings to None for nullable fields
        nullable_fields = [
            'date_of_birth', 'contact', 'grade_id', 'department_id', 'position',
            'date_joined', 'origin_structure', 'workplace', 'region',
            'qualification_category', 'current_class', 'echelon'
        ]
        for field in nullable_fields:
            if field in data and data[field] == '':
                data[field] = None
        return data
        
        
        