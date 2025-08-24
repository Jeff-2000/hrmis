from rest_framework import serializers
from payroll.models import PayrollRun, Payslip, PayslipItem, PayrollComponent, CompanyPolicy, Currency
from employee.models import Employee
from attendance.models import AttendanceRecord
from django.utils import timezone
from decimal import Decimal
from django.db import transaction

# ----- Payroll upload -----

class PayslipItemInSerializer(serializers.Serializer):
    component_code = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))
    rate = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    meta = serializers.DictField(required=False)

class PayslipInSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    base_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    items = PayslipItemInSerializer(many=True, required=False, default=list)
    other_deductions = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0"))

class PayrollUploadSerializer(serializers.Serializer):
    company_policy_id = serializers.IntegerField()
    year = serializers.IntegerField(min_value=1900, max_value=3000)
    month = serializers.IntegerField(min_value=1, max_value=12)
    currency_id = serializers.CharField(max_length=3)
    payslips = PayslipInSerializer(many=True)

    def validate(self, data):
        # validate foreign keys
        try:
            data["company_policy"] = CompanyPolicy.objects.get(id=data["company_policy_id"])
        except CompanyPolicy.DoesNotExist:
            raise serializers.ValidationError({"company_policy_id": "Invalid company policy."})
        try:
            data["currency"] = Currency.objects.get(pk=data["currency_id"])
        except Currency.DoesNotExist:
            raise serializers.ValidationError({"currency_id": "Invalid currency code."})
        return data

    @transaction.atomic
    def create(self, validated):
        cp = validated["company_policy"]
        year = validated["year"]
        month = validated["month"]
        currency = validated["currency"]

        run, _ = PayrollRun.objects.get_or_create(
            company_policy=cp, year=year, month=month,
            defaults={}
        )

        created, updated, errors = 0, 0, []

        for ps in validated["payslips"]:
            emp_id = ps["employee_id"]
            try:
                employee = Employee.objects.get(id=emp_id)
            except Employee.DoesNotExist:
                errors.append({"employee_id": str(emp_id), "error": "Employee not found"})
                continue

            payslip, was_created = Payslip.objects.get_or_create(
                run=run, employee=employee,
                defaults={"currency": currency, "base_salary": ps["base_salary"]}
            )
            if not was_created:
                payslip.currency = currency
                payslip.base_salary = ps["base_salary"]

            # Reset computed fields
            payslip.gross_pay = Decimal("0")
            payslip.taxable_gross = Decimal("0")
            payslip.employee_contrib = Decimal("0")
            payslip.employer_contrib = Decimal("0")
            payslip.income_tax = Decimal("0")
            payslip.other_deductions = ps.get("other_deductions") or Decimal("0")
            payslip.net_pay = Decimal("0")
            payslip.finalized = False
            payslip.save()

            # Clear & recreate items
            payslip.items.all().delete()
            for item in ps.get("items", []):
                try:
                    comp = PayrollComponent.objects.get(code=item["component_code"])
                except PayrollComponent.DoesNotExist:
                    errors.append({"employee_id": str(emp_id), "component_code": item["component_code"], "error": "Component not found"})
                    continue
                pi = PayslipItem.objects.create(
                    payslip=payslip, component=comp,
                    quantity=item.get("quantity") or Decimal("1"),
                    rate=item.get("rate") or Decimal("0"),
                    amount=item["amount"],
                    meta=item.get("meta") or {},
                )
                # Basic aggregation (you can improve logic later)
                if comp.kind == PayrollComponent.EARNING:
                    payslip.gross_pay += pi.amount
                    payslip.taxable_gross += (pi.amount if comp.taxable else Decimal("0"))
                elif comp.kind == PayrollComponent.DEDUCTION:
                    payslip.other_deductions += pi.amount
                elif comp.kind == PayrollComponent.EMPLOYER:
                    payslip.employer_contrib += pi.amount

            # Compute net pay (simplified)
            payslip.net_pay = payslip.gross_pay - payslip.employee_contrib - payslip.income_tax - payslip.other_deductions
            payslip.save()

            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        return {"run_id": run.id, "created": created, "updated": updated, "errors": errors}


# ----- Disbursement callback -----

class DisbursementItemSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["PAID", "FAILED", "PARTIAL"])
    reference = serializers.CharField(required=False, allow_blank=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)

class PayrollDisbursementSerializer(serializers.Serializer):
    run_id = serializers.IntegerField()
    bank_batch_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["SUCCESS", "PARTIAL", "FAILED"])
    details = DisbursementItemSerializer(many=True)

    def save(self, **kwargs):
        from payroll.models import Payslip, PayrollRun
        try:
            run = PayrollRun.objects.get(id=self.validated_data["run_id"])
        except PayrollRun.DoesNotExist:
            raise serializers.ValidationError({"run_id": "Invalid payroll run."})

        updated, errors = 0, []

        for d in self.validated_data["details"]:
            try:
                ps = Payslip.objects.get(run=run, employee_id=d["employee_id"])
            except Payslip.DoesNotExist:
                errors.append({"employee_id": str(d["employee_id"]), "error": "Payslip not found for run"})
                continue

            # Minimal reconciliation: mark finalized if PAID or PARTIAL
            if d["status"] in ("PAID", "PARTIAL"):
                ps.finalized = True
                ps.save(update_fields=["finalized"])
                updated += 1

        # Store status note on run
        run.note = f"Bank batch {self.validated_data['bank_batch_id']} status={self.validated_data['status']}"
        run.save(update_fields=["note"])
        return {"updated": updated, "errors": errors}


# ----- Attendance (biometric punches) -----

class PunchSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    timestamp = serializers.DateTimeField()
    event = serializers.ChoiceField(choices=["IN", "OUT"])

    def save(self, **kwargs):
        from django.utils import timezone
        from datetime import datetime
        from employee.models import Employee
        from attendance.models import AttendanceRecord

        emp = Employee.objects.filter(id=self.validated_data["employee_id"]).first()
        if not emp:
            raise serializers.ValidationError({"employee_id": "Employee not found"})

        ts = self.validated_data["timestamp"].astimezone(timezone.get_current_timezone())
        d = ts.date()
        rec, _ = AttendanceRecord.objects.get_or_create(employee=emp, date=d)

        if self.validated_data["event"] == "IN":
            if rec.check_in is None or ts.time() < rec.check_in:
                rec.check_in = ts.time()
        else:
            if rec.check_out is None or ts.time() > rec.check_out:
                rec.check_out = ts.time()

        # derive status (simple)
        rec.status = "present"
        rec.save()
        return {"attendance_id": rec.id, "date": str(rec.date)}

class PunchBulkSerializer(serializers.Serializer):
    punches = PunchSerializer(many=True)

    def save(self, **kwargs):
        created, errors = 0, []
        for p in self.validated_data["punches"]:
            try:
                PunchSerializer(data=p).is_valid(raise_exception=True)
                res = PunchSerializer(data=p)
                res.is_valid(raise_exception=True)
                res.save()
                created += 1
            except serializers.ValidationError as e:
                errors.append({"punch": p, "error": e.detail})
        return {"created": created, "errors": errors}
