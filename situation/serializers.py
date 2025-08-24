# situation/serializers.py
from rest_framework import serializers
from .models import Situation
from payroll.serializers import SituationTypeSerializer
from documents.serializers import DocumentSerializer
from employee.serializers import EmployeeSerializer

# class SituationSerializer(serializers.ModelSerializer):
#     employee = EmployeeSerializer(read_only=True)
#     situation_type = SituationTypeSerializer(read_only=True)
#     document = DocumentSerializer(read_only=True)
#     employee_id = serializers.PrimaryKeyRelatedField(
#         queryset='employee.Employee.objects.all()', source='employee', write_only=True
#     )
#     situation_type_id = serializers.PrimaryKeyRelatedField(
#         queryset='payroll.SituationType.objects.all()', source='situation_type', write_only=True
#     )
#     document_id = serializers.PrimaryKeyRelatedField(
#         queryset='documents.Document.objects.all()', source='document', write_only=True, required=False
#     )

#     class Meta:
#         model = Situation
#         fields = '__all__'

#     def validate(self, data):
#         start = data.get('start_date')
#         end = data.get('end_date')
#         if start and end and start > end:
#             raise serializers.ValidationError("End date must be after start date.")
#         return data


# situation/serializers.py
from rest_framework import serializers
from .models import Situation
from payroll.serializers import SituationTypeSerializer
from documents.serializers import DocumentSerializer
from employee.serializers import EmployeeSerializer
from employee.models import Employee
from payroll.models import SituationType
from documents.models import Document

class SituationSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    situation_type = SituationTypeSerializer(read_only=True)
    document = DocumentSerializer(read_only=True)

    # write-only helpers
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )
    situation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SituationType.objects.all(), source='situation_type', write_only=True
    )
    document_id = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), source='document', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Situation
        fields = '__all__'

    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        if start and end and start > end:
            raise serializers.ValidationError("End date must be after start date.")
        # Ensure tranches (if provided) make sense (pairs + within [start,end])
        win_start = start or getattr(self.instance, 'start_date', None)
        win_end   = end or getattr(self.instance, 'end_date', None)
        for i in (1, 2, 3):
            s = data.get(f'tranche_{i}_start')
            e = data.get(f'tranche_{i}_end')
            if (s and not e) or (e and not s):
                raise serializers.ValidationError(f"Tranche {i}: both start and end are required.")
            if s and e and s > e:
                raise serializers.ValidationError(f"Tranche {i}: start must be before end.")
            if s and win_start and s < win_start:
                raise serializers.ValidationError(f"Tranche {i}: start must be ≥ situation start.")
            if e and win_end and e > win_end:
                raise serializers.ValidationError(f"Tranche {i}: end must be ≤ situation end.")
        return data


