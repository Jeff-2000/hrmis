from django.core.management.base import BaseCommand
from django.utils import timezone
from payroll.models import (
    PayrollComponent, TaxTable, TaxBracket, ContributionScheme, Currency, ExchangeRate,
    CompanyPolicy, PayrollRun, Payslip, PayslipItem
)
from employee.models import Employee
from decimal import Decimal
from datetime import date
import uuid

class Command(BaseCommand):
    help = 'Populates payroll-related models with sample data for testing'

    def handle(self, *args, **kwargs):
        # Step 1: Create Currencies
        currencies_data = [
            {'code': 'XOF', 'name': 'West African CFA Franc'},
            {'code': 'USD', 'name': 'US Dollar'},
        ]
        for data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=data['code'], defaults={'name': data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Currency: {currency.code} - {currency.name}"))

        # Step 2: Create Exchange Rates
        xof = Currency.objects.get(code='XOF')
        usd = Currency.objects.get(code='USD')
        exchange_rates_data = [
            {
                'base': xof,
                'quote': usd,
                'date': date(2025, 8, 1),
                'rate': Decimal('0.0017')  # Approx 600 XOF = 1 USD
            },
        ]
        for data in exchange_rates_data:
            er, created = ExchangeRate.objects.get_or_create(
                base=data['base'], quote=data['quote'], date=data['date'],
                defaults={'rate': data['rate']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ExchangeRate: {er.base.code}/{er.quote.code} on {er.date}"))

        # Step 3: Create Payroll Components
        components_data = [
            {'code': 'BASIC', 'name': 'Basic Salary', 'kind': 'EARNING', 'taxable': True, 'contributory': True, 'percentage': None, 'sequence': 10},
            {'code': 'OVERTIME', 'name': 'Overtime Pay', 'kind': 'EARNING', 'taxable': True, 'contributory': True, 'percentage': Decimal('0.0150'), 'sequence': 20},
            {'code': 'ALW_TRANSPORT', 'name': 'Transport Allowance', 'kind': 'EARNING', 'taxable': True, 'contributory': False, 'percentage': None, 'sequence': 30},
            {'code': 'TAX_PIT', 'name': 'Personal Income Tax', 'kind': 'DEDUCTION', 'taxable': False, 'contributory': False, 'percentage': None, 'sequence': 100},
            {'code': 'PENSION_EE', 'name': 'Employee Pension Contribution', 'kind': 'DEDUCTION', 'taxable': False, 'contributory': True, 'percentage': Decimal('0.0740'), 'sequence': 110},
            {'code': 'PENSION_ER', 'name': 'Employer Pension Contribution', 'kind': 'EMPLOYER', 'taxable': False, 'contributory': True, 'percentage': Decimal('0.1260'), 'sequence': 120},
            {'code': 'LOAN_REPAY', 'name': 'Loan Repayment', 'kind': 'DEDUCTION', 'taxable': False, 'contributory': False, 'percentage': None, 'sequence': 130},
        ]
        for data in components_data:
            comp, created = PayrollComponent.objects.get_or_create(
                code=data['code'], defaults={
                    'name': data['name'], 'kind': data['kind'], 'taxable': data['taxable'],
                    'contributory': data['contributory'], 'percentage': data['percentage'],
                    'sequence': data['sequence']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created PayrollComponent: {comp.code} - {comp.name}"))

        # Step 4: Create Tax Table and Brackets
        tax_table, created = TaxTable.objects.get_or_create(
            country='CI', valid_from=date(2025, 1, 1), valid_to=None,
            defaults={'country': 'CI', 'valid_from': date(2025, 1, 1)}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created TaxTable: CI {tax_table.valid_from}"))

        brackets_data = [
            {'table': tax_table, 'lower': Decimal('0.00'), 'upper': Decimal('600000.00'), 'rate': Decimal('0.0000')},
            {'table': tax_table, 'lower': Decimal('600001.00'), 'upper': Decimal('1560000.00'), 'rate': Decimal('0.1500')},
            {'table': tax_table, 'lower': Decimal('1560001.00'), 'upper': Decimal('3000000.00'), 'rate': Decimal('0.2500')},
            {'table': tax_table, 'lower': Decimal('3000001.00'), 'upper': None, 'rate': Decimal('0.3500')},
        ]
        for data in brackets_data:
            bracket, created = TaxBracket.objects.get_or_create(
                table=data['table'], lower=data['lower'],
                defaults={'upper': data['upper'], 'rate': data['rate']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created TaxBracket: {bracket.lower} - {bracket.upper or '∞'} at {bracket.rate*100}%"))

        # Step 5: Create Contribution Schemes
        contrib_schemes_data = [
            {
                'code': 'PENSION_CI', 'name': "Côte d'Ivoire Pension Scheme",
                'ee_rate': Decimal('0.0740'), 'er_rate': Decimal('0.1260'), 'valid_from': date(2025, 1, 1),
                'valid_to': None, 'cap': Decimal('1625000.00'), 'include_taxable_allowances': True
            },
            {
                'code': 'HEALTH_CI', 'name': "Côte d'Ivoire Health Scheme",
                'ee_rate': Decimal('0.0350'), 'er_rate': Decimal('0.0350'), 'valid_from': date(2025, 1, 1),
                'valid_to': None, 'cap': Decimal('1000000.00'), 'include_taxable_allowances': True
            },
        ]
        for data in contrib_schemes_data:
            scheme, created = ContributionScheme.objects.get_or_create(
                code=data['code'], defaults={
                    'name': data['name'], 'ee_rate': data['ee_rate'], 'er_rate': data['er_rate'],
                    'valid_from': data['valid_from'], 'valid_to': data['valid_to'],
                    'cap': data['cap'], 'include_taxable_allowances': data['include_taxable_allowances']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ContributionScheme: {scheme.code} - {scheme.name}"))

        # Step 6: Create Company Policy
        company_policy, created = CompanyPolicy.objects.get_or_create(
            name='Default Policy CI', defaults={
                'country': 'CI', 'currency': xof, 'proration_method': 'CALENDAR',
                'active_tax_table': tax_table
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created CompanyPolicy: {company_policy.name}"))
        company_policy.active_contribs.add(*ContributionScheme.objects.all())

        # Step 7: Create Payroll Run
        payroll_run, created = PayrollRun.objects.get_or_create(
            company_policy=company_policy, year=2025, month=8, defaults={
                'status': 'DRAFT', 'note': 'August 2025 Payroll Run'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created PayrollRun: {payroll_run}"))

        # Step 8: Create Payslips and Payslip Items
        # Replace these UUIDs with actual employee UUIDs from your database
        employees_data = [
            {
                'employee_id': uuid.UUID('e19702f6-8620-4d3e-8f1c-4bb66e7bae04'),  # Replace with actual UUID
                'base_salary': Decimal('1000000.00'),
                'payslip_items': [
                    {'component_code': 'BASIC', 'quantity': Decimal('1.000'), 'rate': Decimal('1000000.00'), 'amount': Decimal('1000000.00'), 'meta': {'note': 'Monthly base salary'}},
                    {'component_code': 'OVERTIME', 'quantity': Decimal('10.000'), 'rate': Decimal('15000.00'), 'amount': Decimal('150000.00'), 'meta': {'hours': 10}},
                    {'component_code': 'ALW_TRANSPORT', 'quantity': Decimal('1.000'), 'rate': Decimal('50000.00'), 'amount': Decimal('50000.00'), 'meta': {}},
                    {'component_code': 'TAX_PIT', 'quantity': Decimal('1.000'), 'rate': Decimal('112500.00'), 'amount': Decimal('112500.00'), 'meta': {'taxable_gross': 1050000}},
                    {'component_code': 'PENSION_EE', 'quantity': Decimal('1.000'), 'rate': Decimal('77700.00'), 'amount': Decimal('77700.00'), 'meta': {'base': 1050000}},
                    {'component_code': 'PENSION_ER', 'quantity': Decimal('1.000'), 'rate': Decimal('132300.00'), 'amount': Decimal('132300.00'), 'meta': {'base': 1050000}},
                    {'component_code': 'HEALTH_CI', 'quantity': Decimal('1.000'), 'rate': Decimal('36750.00'), 'amount': Decimal('36750.00'), 'meta': {'base': 1050000}},
                ]
            },
            {
                'employee_id': uuid.UUID('e08bfa9d-d85d-4006-ad77-e7d265b0cc78'),  # Replace with actual UUID
                'base_salary': Decimal('800000.00'),
                'payslip_items': [
                    {'component_code': 'BASIC', 'quantity': Decimal('1.000'), 'rate': Decimal('800000.00'), 'amount': Decimal('800000.00'), 'meta': {'note': 'Monthly base salary'}},
                    {'component_code': 'ALW_TRANSPORT', 'quantity': Decimal('1.000'), 'rate': Decimal('40000.00'), 'amount': Decimal('40000.00'), 'meta': {}},
                    {'component_code': 'TAX_PIT', 'quantity': Decimal('1.000'), 'rate': Decimal('66000.00'), 'amount': Decimal('66000.00'), 'meta': {'taxable_gross': 840000}},
                    {'component_code': 'PENSION_EE', 'quantity': Decimal('1.000'), 'rate': Decimal('62160.00'), 'amount': Decimal('62160.00'), 'meta': {'base': 840000}},
                    {'component_code': 'PENSION_ER', 'quantity': Decimal('1.000'), 'rate': Decimal('105840.00'), 'amount': Decimal('105840.00'), 'meta': {'base': 840000}},
                    {'component_code': 'HEALTH_CI', 'quantity': Decimal('1.000'), 'rate': Decimal('29400.00'), 'amount': Decimal('29400.00'), 'meta': {'base': 840000}},
                    {'component_code': 'LOAN_REPAY', 'quantity': Decimal('1.000'), 'rate': Decimal('50000.00'), 'amount': Decimal('50000.00'), 'meta': {'loan_id': 1}},
                ]
            },
            {
                'employee_id': uuid.UUID('f7a05ba0-2a44-477e-b4d6-01ea53655bd7'),  # Replace with actual UUID
                'base_salary': Decimal('1200000.00'),
                'payslip_items': [
                    {'component_code': 'BASIC', 'quantity': Decimal('1.000'), 'rate': Decimal('1200000.00'), 'amount': Decimal('1200000.00'), 'meta': {'note': 'Monthly base salary'}},
                    {'component_code': 'OVERTIME', 'quantity': Decimal('5.000'), 'rate': Decimal('18000.00'), 'amount': Decimal('90000.00'), 'meta': {'hours': 5}},
                    {'component_code': 'ALW_TRANSPORT', 'quantity': Decimal('1.000'), 'rate': Decimal('60000.00'), 'amount': Decimal('60000.00'), 'meta': {}},
                    {'component_code': 'TAX_PIT', 'quantity': Decimal('1.000'), 'rate': Decimal('154500.00'), 'amount': Decimal('154500.00'), 'meta': {'taxable_gross': 1350000}},
                    {'component_code': 'PENSION_EE', 'quantity': Decimal('1.000'), 'rate': Decimal('99900.00'), 'amount': Decimal('99900.00'), 'meta': {'base': 1350000}},
                    {'component_code': 'PENSION_ER', 'quantity': Decimal('1.000'), 'rate': Decimal('170100.00'), 'amount': Decimal('170100.00'), 'meta': {'base': 1350000}},
                    {'component_code': 'HEALTH_CI', 'quantity': Decimal('1.000'), 'rate': Decimal('35000.00'), 'amount': Decimal('35000.00'), 'meta': {'base': 1000000}},  # Capped at 1M
                ]
            },
        ]

        created_payslips = 0
        for emp_data in employees_data:
            try:
                employee = Employee.objects.get(id=emp_data['employee_id'])
                payslip, created = Payslip.objects.get_or_create(
                    run=payroll_run, employee=employee, defaults={
                        'base_salary': emp_data['base_salary'],
                        'gross_pay': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['BASIC', 'OVERTIME', 'ALW_TRANSPORT']),
                        'taxable_gross': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['BASIC', 'OVERTIME', 'ALW_TRANSPORT']),
                        'employee_contrib': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['PENSION_EE', 'HEALTH_CI']),
                        'employer_contrib': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['PENSION_ER']),
                        'income_tax': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] == 'TAX_PIT'),
                        'other_deductions': sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] == 'LOAN_REPAY'),
                        'net_pay': (
                            sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['BASIC', 'OVERTIME', 'ALW_TRANSPORT']) -
                            sum(item['amount'] for item in emp_data['payslip_items'] if item['component_code'] in ['TAX_PIT', 'PENSION_EE', 'HEALTH_CI', 'LOAN_REPAY'])
                        ),
                        'currency': xof,
                        'finalized': False
                    }
                )
                if created:
                    created_payslips += 1
                    self.stdout.write(self.style.SUCCESS(f"Created Payslip: {payslip.employee} for {payslip.run}"))

                for item_data in emp_data['payslip_items']:
                    component = PayrollComponent.objects.get(code=item_data['component_code'])
                    PayslipItem.objects.get_or_create(
                        payslip=payslip, component=component,
                        defaults={
                            'quantity': item_data['quantity'],
                            'rate': item_data['rate'],
                            'amount': item_data['amount'],
                            'meta': item_data['meta']
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created PayslipItem: {component.code} for {payslip.employee}"))
            except Employee.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Employee with ID {emp_data['employee_id']} does not exist."))
            except PayrollComponent.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"PayrollComponent with code {item_data['component_code']} does not exist."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating payslip for employee ID {emp_data['employee_id']}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_payslips} payslips."))