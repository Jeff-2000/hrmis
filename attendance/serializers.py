# attendance/serializers.py
from rest_framework import serializers
from .models import AttendanceRecord
from employee.models import Employee

class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employee', 'date', 'check_in', 'check_out', 'status']
        read_only_fields = ['id']
        extra_kwargs = {
            'employee': {'read_only': True},
            #'date': {'required': False},
            'check_in': {'required': False},
            'check_out': {'required': False},
            #'status': {'required': False}
        }

    def get_employee(self, obj):
        return {
            'id': str(obj.employee.id),
            'first_name': obj.employee.first_name,
            'last_name': obj.employee.last_name
        }

    def validate(self, data):
        # Ensure unique employee-date combination
        if self.instance is None:  # Create
            if AttendanceRecord.objects.filter(
                employee_id=data['employee'].id,
                date=data['date']
            ).exists():
                raise serializers.ValidationError({'error': 'Un enregistrement existe déjà pour cet employé et cette date.'})
        return data

    def create(self, validated_data):
        return AttendanceRecord.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.check_in = validated_data.get('check_in', instance.check_in)
        instance.check_out = validated_data.get('check_out', instance.check_out)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance