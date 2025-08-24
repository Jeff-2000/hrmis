from django.contrib import admin
from .models import *

@admin.register(SituationType)
class SituationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'suspend_payroll')
    search_fields = ('name', 'code')
    list_filter = ('suspend_payroll',)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'base_salary', 'allowances', 'deductions', 'net_pay', 'status', 'generated_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__id')
    list_filter = ('status', 'year', 'month')
    date_hierarchy = 'generated_at'
    ordering = ('-year', '-month')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('employee', 'contract_type', 'salary', 'start_date', 'end_date', 'status', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name', 'contract_type')
    list_filter = ('contract_type', 'status', 'start_date', 'end_date')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)



# ---------------------
# Inlines
# ---------------------

class TaxBracketInline(admin.TabularInline):
    model = TaxBracket
    extra = 1


class PayslipItemInline(admin.TabularInline):
    model = PayslipItem
    extra = 0


# ---------------------
# Admin registrations
# ---------------------

@admin.register(PayrollComponent)
class PayrollComponentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'kind', 'taxable', 'contributory', 'percentage', 'sequence')
    list_filter = ('kind', 'taxable', 'contributory')
    search_fields = ('code', 'name')
    ordering = ('sequence', 'code')


@admin.register(TaxTable)
class TaxTableAdmin(admin.ModelAdmin):
    list_display = ('country', 'valid_from', 'valid_to')
    list_filter = ('country',)
    inlines = [TaxBracketInline]


@admin.register(ContributionScheme)
class ContributionSchemeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'ee_rate', 'er_rate', 'valid_from', 'valid_to', 'cap', 'include_taxable_allowances')
    list_filter = ('include_taxable_allowances',)
    search_fields = ('code', 'name')


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('base', 'quote', 'date', 'rate')
    list_filter = ('base', 'quote', 'date')
    search_fields = ('base__code', 'quote__code')
    ordering = ('-date',)


@admin.register(CompanyPolicy)
class CompanyPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'currency', 'proration_method')
    list_filter = ('country', 'proration_method')
    filter_horizontal = ('active_contribs',)
    search_fields = ('name',)


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ('company_policy', 'year', 'month', 'status', 'generated_at', 'processed_at', 'closed_at')
    list_filter = ('status', 'year', 'month', 'company_policy')
    search_fields = ('company_policy__name',)
    date_hierarchy = 'generated_at'
    ordering = ('-year', '-month')


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'run', 'gross_pay', 'net_pay', 'currency', 'finalized', 'created_at')
    list_filter = ('finalized', 'currency', 'run__company_policy')
    search_fields = ('employee__first_name', 'employee__last_name', 'run__company_policy__name')
    inlines = [PayslipItemInline]
    date_hierarchy = 'created_at'


# No need to register PayslipItem separately since it's inline in Payslip

