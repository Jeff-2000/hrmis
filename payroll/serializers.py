# payroll/serializers.py
from rest_framework import serializers
from .models import PayrollRecord
# To delete
class PayrollRecordSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField()  # or use EmployeeSerializer for details
    class Meta:
        model = PayrollRecord
        fields = ['id', 'employee', 'period', 'base_salary', 'allowances', 'deductions', 'net_salary', 'paid', 'created_at']
        read_only_fields = ['id', 'net_salary', 'created_at']



# payroll/serializers.py
from rest_framework import serializers
from .models import SituationType, Payroll
from employee.serializers import EmployeeSerializer

class SituationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationType
        fields = '__all__'

class PayrollSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset='employee.Employee.objects.all()', source='employee', write_only=True
    )

    class Meta:
        model = Payroll
        fields = '__all__'
        read_only_fields = ['net_pay', 'generated_at']

    def validate(self, data):
        if 'month' in data and not (1 <= data['month'] <= 12):
            raise serializers.ValidationError("Month must be between 1 and 12.")
        return data


# payroll/serializers.py (extend)

from rest_framework import serializers
from .models import *
from employee.serializers import EmployeeSerializer

from rest_framework import serializers

from employee.serializers import EmployeeSerializer

# Already present:
class PayrollComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollComponent
        fields = '__all__'

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class ExchangeRateSerializer(serializers.ModelSerializer):
    base = CurrencySerializer(read_only=True)
    quote = CurrencySerializer(read_only=True)
    base_id  = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), source='base', write_only=True)
    quote_id = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), source='quote', write_only=True)

    class Meta:
        model = ExchangeRate
        fields = ['id','base','quote','base_id','quote_id','date','rate']

class ContributionSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionScheme
        fields = '__all__'

class TaxBracketSerializer(serializers.ModelSerializer):
    table_id = serializers.PrimaryKeyRelatedField(queryset=TaxTable.objects.all(), source='table', write_only=True)
    class Meta:
        model = TaxBracket
        fields = ['id','table_id','lower','upper','rate']

class TaxTableSerializer(serializers.ModelSerializer):
    brackets = TaxBracketSerializer(many=True, read_only=True)
    class Meta:
        model = TaxTable
        fields = ['id','country','valid_from','valid_to','brackets']

class CompanyPolicySerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), source='currency', write_only=True)
    active_tax_table = TaxTableSerializer(read_only=True)
    active_tax_table_id = serializers.PrimaryKeyRelatedField(queryset=TaxTable.objects.all(), source='active_tax_table', write_only=True, required=False, allow_null=True)
    active_contribs = ContributionSchemeSerializer(many=True, read_only=True)
    active_contribs_ids = serializers.PrimaryKeyRelatedField(queryset=ContributionScheme.objects.all(), many=True, write_only=True, required=False, source='active_contribs')

    class Meta:
        model = CompanyPolicy
        fields = [
            'id','name','country',
            'currency','currency_id',
            'proration_method',
            'active_tax_table','active_tax_table_id',
            'active_contribs','active_contribs_ids'
        ]


# (If you’re using the Run/Payslip part from earlier)
class PayrollRunSerializer(serializers.ModelSerializer):
    company_policy = CompanyPolicySerializer(read_only=True)
    company_policy_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyPolicy.objects.all(), source='company_policy', write_only=True
    )
    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = ['status','generated_at','processed_at','closed_at']

class PayslipItemSerializer(serializers.ModelSerializer):
    component = PayrollComponentSerializer(read_only=True)
    component_id = serializers.PrimaryKeyRelatedField(queryset=PayrollComponent.objects.all(), source='component', write_only=True)
    class Meta:
        model = PayslipItem
        fields = ['id','component','component_id','quantity','rate','amount','meta']

class PayslipSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    items = PayslipItemSerializer(many=True, read_only=True)
    run = PayrollRunSerializer(read_only=True)  # <-- now run has month/year
    # optional: keep a write-only run_id if you ever need to POST/PATCH
    run_id = serializers.PrimaryKeyRelatedField(
        queryset=PayrollRun.objects.all(), source='run', write_only=True, required=False
    )
    period = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = [
            'id','run','run_id','employee',
            'base_salary','gross_pay','taxable_gross',
            'employee_contrib','employer_contrib','income_tax',
            'other_deductions','net_pay','currency',
            'finalized','created_at','updated_at','hash',
            'items','period'
        ]
        read_only_fields = [
            'gross_pay','taxable_gross','employee_contrib','employer_contrib',
            'income_tax','other_deductions','net_pay','finalized',
            'created_at','updated_at','hash','items','employee','run'
        ]

    def get_period(self, obj):
        try:
            return f"{obj.run.month:02d}/{obj.run.year}"
        except Exception:
            return ""


class VariableInputSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )
    component = PayrollComponentSerializer(read_only=True)
    component_id = serializers.PrimaryKeyRelatedField(
        queryset=PayrollComponent.objects.all(), source='component', write_only=True
    )
    run_id = serializers.PrimaryKeyRelatedField(
        queryset=PayrollRun.objects.all(), source='run', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = VariableInput
        fields = ['id', 'run', 'run_id', 'employee', 'employee_id', 'component', 'component_id',
                  'quantity', 'rate', 'amount', 'note', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at', 'run']

    def create(self, validated):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated['created_by'] = request.user
        return super().create(validated)


class RecurringComponentAssignmentSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )
    component = PayrollComponentSerializer(read_only=True)
    component_id = serializers.PrimaryKeyRelatedField(
        queryset=PayrollComponent.objects.all(), source='component', write_only=True
    )

    class Meta:
        model = RecurringComponentAssignment
        fields = ['id', 'employee', 'employee_id', 'component', 'component_id',
                  'amount', 'percentage', 'start_date', 'end_date', 'note', 'active', 'created_at']
        read_only_fields = ['created_at']


class ContractSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )

    class Meta:
        model = Contract
        fields = '__all__'









