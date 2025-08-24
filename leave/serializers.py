# leave/serializers.py
from rest_framework import serializers
from .models import *
from employee.models import *
from employee.serializers import EmployeeSerializer
from documents.serializers import DocumentSerializer
from datetime import datetime


# leave/serializers.py
from rest_framework import serializers
from .models import *
from employee.models import Employee
from employee.serializers import EmployeeSerializer
from documents.models import Document
from documents.serializers import DocumentSerializer
from authentication.models import User

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class UserMinimalSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role']

    def get_first_name(self, obj):
        if obj.first_name and obj.first_name.strip():
            return obj.first_name
        employee = getattr(obj, 'employee', None)
        if employee and employee.first_name and employee.first_name.strip():
            return employee.first_name
        return ''

    def get_last_name(self, obj):
        if obj.last_name and obj.last_name.strip():
            return obj.last_name
        employee = getattr(obj, 'employee', None)
        if employee and employee.last_name and employee.last_name.strip():
            return employee.last_name
        return ''

class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type = LeaveTypeSerializer(read_only=True)
    leave_type_id = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(), source='leave_type', write_only=True
    )

    class Meta:
        model = LeaveBalance
        fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    approved_by = UserMinimalSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)
    leave_type = LeaveTypeSerializer(read_only=True)
    document = DocumentSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )
    leave_type_id = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(), source='leave_type', write_only=True
    )
    document_id = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), source='document', write_only=True, required=False
    )
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    calculate_working_days = serializers.ReadOnlyField(source='calculate_working_days_property')

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ['status', 'approved_by', 'requested_at', 'employee', 'leave_type', 'document', 'calculate_working_days', 'is_read']

    def validate(self, data):
        # Only validate start_date and end_date if both are provided
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Start date must be before end date.")
        
        # Only validate leave_type and document if leave_type is provided
        if 'leave_type' in data:
            if data['leave_type'].requires_attachment and not data.get('document') and not self.instance:
                raise serializers.ValidationError("This leave type requires a document.")
        
        # Validate for overlapping situations if employee and dates are provided
        if 'employee' in data and 'start_date' in data and 'end_date' in data:
            from situation.models import Situation
            overlapping = Situation.objects.filter(
                employee=data['employee'],
                situation_type__code__in=['sick_leave', 'maternity_leave', 'parental_leave'],
                start_date__lte=data['end_date'],
                end_date__gte=data['start_date']
            ).exists()
            if overlapping:
                raise serializers.ValidationError("Conflit avec une situation administrative existante.")
        
        return data

    def create(self, validated_data):
        # Create the leave request
        leave_request = super().create(validated_data)
        # If document_id is provided, update the document's content_type and object_id
        if validated_data.get('document'):
            document = validated_data['document']
            document.content_type = ContentType.objects.get_for_model(LeaveRequest)
            document.object_id = leave_request.id
            document.save()
        return leave_request


class LeaveEventSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    start = serializers.DateField(source="start_date")
    end = serializers.SerializerMethodField()  # exclusive end for FullCalendar
    extendedProps = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ("id", "title", "start", "end", "extendedProps")

    def get_title(self, obj):
        # adjust as you like
        return f"{obj.employee.get_full_name()} — {obj.leave_type.name}"

    def get_end(self, obj):
        # FullCalendar treats end as exclusive for all-day ranges
        return obj.end_date + datetime.timedelta(days=1)

    def get_extendedProps(self, obj):
        return {
            "status": obj.status,
            "reason": obj.reason,
            "rejection_reason": obj.rejection_reason,
            "employee": {
                "id": obj.employee.id,
                "first_name": obj.employee.first_name,
                "last_name": obj.employee.last_name,
                "user": {"id": obj.employee.user_id},
                # add manager if you need it on the client:
                "manager": {"user": {"id": getattr(getattr(obj.employee, "manager", None), "user_id", None)}}
            },
            "leave_type": {"id": obj.leave_type_id, "name": obj.leave_type.name},
        }




