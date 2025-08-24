# payroll/models.py
from django.db import models
# To delete
class PayrollRecord(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    period = models.DateField(help_text="Salary period (e.g. first day of month)")
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.BooleanField(default=False, help_text="Whether the salary is paid out")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'period')  # one record per employee per period

    def __str__(self):
        return f"{self.employee} - {self.period.strftime('%Y-%m')} : {self.net_salary}"



from django.db import models
from django.utils import timezone
from employee.models import Employee

class SituationType(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    suspend_payroll = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Payroll(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
    ]

    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'year', 'month')

    def __str__(self):
        return f"{self.employee} - {self.month}/{self.year} ({self.status})"

    def save(self, *args, **kwargs):
        # Compute net_pay before saving
        self.net_pay = self.base_salary + self.allowances - self.deductions
        super().save(*args, **kwargs)
        
class Contract(models.Model):
    """Tracks employee contracts and salary history."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=50, choices=[
        ('PERMANENT', 'Fonctionnaire (Permanent)'),
        ('CONTRACTUAL', 'Agent contractuel'),
        ('TEMPORARY', 'Temporaire'),
    ], help_text="Type of contract")
    salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly salary in local currency")
    start_date = models.DateField(help_text="Contract start date")
    end_date = models.DateField(null=True, blank=True, help_text="Contract end date, null for ongoing")
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
    ], default='ACTIVE', help_text="Contract status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Additional contract details, e.g., promotion or salary adjustment")
    document = models.ForeignKey('documents.Document', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(fields=['employee', 'start_date'], name='unique_employee_contract_start_date')
        ]
        indexes = [
            models.Index(fields=['start_date','end_date']), # NEW
        ]

    def __str__(self):
        return f"{self.employee} - {self.contract_type} ({self.start_date})"

    def is_active(self):
        today = timezone.now().date()
        return (self.status == 'ACTIVE' and
                self.start_date <= today and
                (self.end_date is None or self.end_date >= today))



# payroll/models.py (additions)

# --- Catalog/config ---

class PayrollComponent(models.Model):
    """
    Catalog of earnings/deductions (e.g., BASIC, OVERTIME, ALW_TRANSPORT, TAX_PIT, PENSION_EE, PENSION_ER, LOAN_REPAY, etc.)
    """
    EARNING = 'EARNING'; DEDUCTION = 'DEDUCTION'; EMPLOYER = 'EMPLOYER'
    KIND_CHOICES = [(EARNING,'Earning'), (DEDUCTION,'Deduction'), (EMPLOYER,'Employer Charge')]
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=EARNING)
    taxable = models.BooleanField(default=True)
    contributory = models.BooleanField(default=True)  # included in contrib base?
    percentage = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True,
                                     help_text="If fixed % of a base; else leave null")
    # ordering for display on payslip
    sequence = models.PositiveIntegerField(default=100)

    def __str__(self): return f"{self.code} - {self.name}"


class TaxTable(models.Model):
    """
    Progressive tax brackets; country-specific. Keep multiple effective periods.
    """
    country = models.CharField(max_length=2, default='XX')
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-valid_from']

class TaxBracket(models.Model):
    table = models.ForeignKey(TaxTable, on_delete=models.CASCADE, related_name='brackets')
    lower = models.DecimalField(max_digits=12, decimal_places=2)
    upper = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # null = infinity
    rate = models.DecimalField(max_digits=7, decimal_places=4)  # e.g. 0.15 = 15%

    class Meta:
        ordering = ['lower']


class ContributionScheme(models.Model):
    """
    Statutory/social contributions (employee/employer rates) and base definition.
    """
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    ee_rate = models.DecimalField(max_digits=7, decimal_places=4)  # employee %
    er_rate = models.DecimalField(max_digits=7, decimal_places=4)  # employer %
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    include_taxable_allowances = models.BooleanField(default=True)

    def __str__(self): return self.name


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)  # ISO 4217
    name = models.CharField(max_length=32)

class ExchangeRate(models.Model):
    base = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='base_rates')
    quote = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='quote_rates')
    date = models.DateField()
    rate = models.DecimalField(max_digits=18, decimal_places=8)

    class Meta:
        unique_together = ('base', 'quote', 'date')


class CompanyPolicy(models.Model):
    """
    Company-level payroll knobs.
    """
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=2, default='XX')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    proration_method = models.CharField(max_length=16, choices=[('CALENDAR','Calendar days'),
                                                                ('WORKING','Working days')], default='CALENDAR')
    # Link active tax table & contribs
    active_tax_table = models.ForeignKey(TaxTable, on_delete=models.SET_NULL, null=True, blank=True)
    active_contribs = models.ManyToManyField(ContributionScheme, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name
    
    class Meta:
        ordering = ['-created_at'] 

# --- Run & results ---

class PayrollRun(models.Model):
    DRAFT='draft'; PROCESSED='processed'; CLOSED='closed'
    STATUS_CHOICES=[(DRAFT,'Draft'),(PROCESSED,'Processed'),(CLOSED,'Closed')]

    company_policy = models.ForeignKey(CompanyPolicy, on_delete=models.PROTECT)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=DRAFT)
    generated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('company_policy', 'year', 'month')
        ordering = ['-year','-month']

    def __str__(self): return f"{self.company_policy} {self.month}/{self.year} ({self.status})"


class Payslip(models.Model):
    """
    A.k.a. payroll result per employee within a run (aka 'Payroll' in your minimal model).
    """
    run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxable_gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_contrib = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_contrib = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hash = models.CharField(max_length=64, blank=True, help_text="Checksum of content for audit")  # optional

    class Meta:
        unique_together = ('run','employee')
        ordering = ['-created_at', '-updated_at']
        indexes = [models.Index(fields=['run'])]  # NEW


    def __str__(self): return f"{self.employee} {self.run.month}/{self.run.year}"



class PayslipItem(models.Model):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(PayrollComponent, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=4, default=0)   # per unit
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    meta = models.JSONField(default=dict, blank=True)  # to store “why/how computed”

    class Meta:
        ordering = ['component__sequence', 'id']
        indexes = [
            models.Index(fields=['payslip','component']),   # NEW
        ]




# --- Monthly variable inputs (overtime, bonus, one-off deductions, etc.) ---
class VariableInput(models.Model):
    run = models.ForeignKey('PayrollRun', on_delete=models.CASCADE, related_name='variables', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='variable_inputs')
    component = models.ForeignKey('PayrollComponent', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee_id', 'component__sequence', 'id']

    def __str__(self):
        return f"{self.employee} {self.component.code} {self.amount}"

# --- Recurring components (monthly allowances / deductions) ---
class RecurringComponentAssignment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='recurring_components')
    component = models.ForeignKey('PayrollComponent', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)  # if % of base salary
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-active', 'component__sequence', 'id']
        unique_together = ('employee', 'component', 'start_date')

    def __str__(self):
        return f"{self.employee} – {self.component.code} ({'active' if self.active else 'inactive'})"

    def is_active_today(self):
        today = timezone.localdate()
        return self.active and self.start_date <= today and (self.end_date is None or self.end_date >= today)


# Optional: add expected cutoff / pay day to CompanyPolicy (safe defaults)
try:
    from django.db.models import F
    if not hasattr(CompanyPolicy, 'cutoff_day'):
        CompanyPolicy.add_to_class('cutoff_day', models.PositiveSmallIntegerField(null=True, blank=True,
            help_text="Day-of-month for payroll cutoff (1-28)."))
    if not hasattr(CompanyPolicy, 'pay_day'):
        CompanyPolicy.add_to_class('pay_day', models.PositiveSmallIntegerField(null=True, blank=True,
            help_text="Target pay date day-of-month (1-28)."))
except Exception:
    # If migrations already added these, ignore
    pass






