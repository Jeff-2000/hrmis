# payroll/services/engine.py

# from dataclasses import dataclass
# from decimal import Decimal, ROUND_HALF_UP
# from datetime import date
# from django.utils import timezone
# from employee.models import Employee
# from situation.models import Situation
# from payroll.models import *
# from django.db import transaction, models

# Q = Decimal

# def round2(x): return (Q(x)).quantize(Q('0.01'), rounding=ROUND_HALF_UP)

# @dataclass
# class Context:
#     employee: Employee
#     run: PayrollRun
#     policy: CompanyPolicy
#     # attach any pre-fetched data you want (contracts, leaves, situations)

# class PayrollEngine:

#     def __init__(self, run: PayrollRun):
#         self.run = run
#         self.policy = run.company_policy

#     def _eligible(self, emp: Employee) -> bool:
#         """Exclude employees with current payroll-suspending situations."""
#         today = timezone.localdate().replace(year=self.run.year, month=self.run.month, day=15)  # mid-month check
#         suspend = Situation.objects.filter(
#             employee=emp,
#             situation_type__suspend_payroll=True,
#             start_date__lte=today
#         ).filter(models.Q(end_date__gte=today) | models.Q(end_date__isnull=True)).exists()
#         return emp.is_active and not suspend

#     def _prorate(self, amount: Decimal, emp: Employee) -> Decimal:
#         """Prorate by calendar days (default) or working days per company policy."""
#         # Calendar-day proration: amount * (eligible_days / total_days_in_month)
#         from calendar import monthrange
#         total_days = monthrange(self.run.year, self.run.month)[1]
#         start = date(self.run.year, self.run.month, 1)
#         end = date(self.run.year, self.run.month, total_days)
#         # Find employment active window in the month (hire/terminate)
#         hire = getattr(emp, 'hire_date', start) or start
#         term = getattr(emp, 'termination_date', None)
#         active_start = max(start, hire)
#         active_end = min(end, term) if term else end
#         active_days = max(0, (active_end - active_start).days + 1)
#         return round2(Q(amount) * Q(active_days) / Q(total_days))

#     def _compute_tax(self, taxable_gross: Decimal) -> Decimal:
#         """Progressive PIT using active tax table."""
#         table = self.policy.active_tax_table
#         if not table: return Q('0.00')
#         tax = Q('0.00')
#         for br in table.brackets.all().order_by('lower'):
#             lower = Q(br.lower)
#             upper = Q(br.upper) if br.upper is not None else None
#             base = taxable_gross
#             if base <= lower: break
#             slab_top = upper if upper is not None else base
#             slab = max(Q('0.00'), min(base, slab_top) - lower)
#             tax += slab * Q(br.rate)
#             if upper is None or base <= upper: break
#         return round2(tax)

#     def _apply_contributions(self, base: Decimal) -> tuple[Decimal, Decimal]:
#         """Sum of EE and ER contributions across active schemes; apply caps."""
#         ee = Q('0.00'); er = Q('0.00')
#         for sch in self.policy.active_contribs.all():
#             contrib_base = min(base, Q(sch.cap)) if sch.cap else base
#             ee += contrib_base * Q(sch.ee_rate)
#             er += contrib_base * Q(sch.er_rate)
#         return round2(ee), round2(er)

#     @transaction.atomic
#     def compute_for_employee(self, emp: Employee) -> Payslip | None:
#         if not self._eligible(emp): return None

#         # Base salary from active contract
#         contract = emp.contracts.filter(status='ACTIVE').order_by('-start_date').first()
#         base = Q(contract.salary if contract else 0)

#         # Prorate base for mid-month entries/exits
#         base_prorated = self._prorate(base, emp)

#         slip, _ = Payslip.objects.get_or_create(
#             run=self.run, employee=emp,
#             defaults={'currency': self.policy.currency}
#         )

#         items = []

#         # BASIC
#         comp_basic = PayrollComponent.objects.get(code='BASIC')
#         items.append(PayslipItem(payslip=slip, component=comp_basic, quantity=1, rate=base_prorated, amount=base_prorated))

#         # TODO: add allowances (transport, housing...) and overtime by reading configured components, timesheets, etc.
#         gross = sum([i.amount for i in items], Q('0.00'))

#         # taxable base: include taxable components only
#         taxable = sum([i.amount for i in items if i.component.taxable], Q('0.00'))

#         # contributions
#         ee_contrib, er_contrib = self._apply_contributions(taxable if self.policy.active_contribs.exists() else Q('0.00'))

#         # income tax
#         pit = self._compute_tax(taxable - ee_contrib)

#         # net pay
#         other_deductions = Q('0.00')  # loans, advances… hook later
#         net = gross - ee_contrib - pit - other_deductions

#         # save slip & items
#         slip.base_salary = round2(base_prorated)
#         slip.gross_pay = round2(gross)
#         slip.taxable_gross = round2(taxable)
#         slip.employee_contrib = round2(ee_contrib)
#         slip.employer_contrib = round2(er_contrib)
#         slip.income_tax = round2(pit)
#         slip.other_deductions = round2(other_deductions)
#         slip.net_pay = round2(net)
#         slip.save()

#         PayslipItem.objects.filter(payslip=slip).delete()
#         PayslipItem.objects.bulk_create(items)

#         return slip

#     @transaction.atomic
#     def compute_run(self):
#         qs = Employee.objects.filter(is_active=True)
#         out = []
#         for emp in qs.select_related('user'):
#             s = self.compute_for_employee(emp)
#             if s: out.append(s.id)
#         self.run.status = 'processed'
#         self.run.processed_at = timezone.now()
#         self.run.save(update_fields=['status','processed_at'])
#         return out



# payroll/services/engine.py

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from calendar import monthrange
from typing import Iterable, Optional, Tuple

from django.db import transaction, models
from django.utils import timezone

from employee.models import Employee

# Optional: suspend-payroll situations (safe if absent)
try:
    from situation.models import Situation  # expected: (employee, situation_type, start_date, end_date)
    HAS_SITUATION = True
except Exception:
    Situation = None
    HAS_SITUATION = False

from payroll.models import *

Q = Decimal
def q2(x) -> Decimal:
    return (Q(x)).quantize(Q("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class Context:
    employee: Employee
    run: PayrollRun
    policy: CompanyPolicy


class PayrollEngine:
    """
    Extended engine:
      - BASIC from active contract (prorated by policy CALENDAR / WORKING)
      - Recurring components (allowances/deductions; amount or % of base)
      - Variable inputs (overtime, bonuses, one-offs) via VariableInput
      - Contributions (EE/ER) from policy.active_contribs, w/ caps
      - PIT from policy.active_tax_table
      - FX via ExchangeRate (base→policy currency), fallback 1:1
      - Employer charges (KIND=EMPLOYER) recorded but excluded from Net
    """

    def __init__(self, run: PayrollRun):
        self.run = run
        self.policy: CompanyPolicy = run.company_policy

    # ---------------- utilities ----------------

    def _period_bounds(self) -> Tuple[date, date, int]:
        days = monthrange(self.run.year, self.run.month)[1]
        start = date(self.run.year, self.run.month, 1)
        end = date(self.run.year, self.run.month, days)
        return start, end, days

    def _working_days_in(self, start: date, end: date) -> int:
        """Mon–Fri count between start..end inclusive."""
        d = start
        n = 0
        while d <= end:
            if d.weekday() < 5:
                n += 1
            d += timedelta(days=1)
        return n

    def _eligible(self, emp: Employee) -> bool:
        """
        Check if employee is eligible for payroll
            - Must be active
            - MUst have no overlapping suspend-payroll situation
        """
        if not getattr(emp, "is_active", True):
            return False
        if not HAS_SITUATION:
            return True
        
        # Payroll period
        pstart, pend, _ = self._period_bounds()

        # We’ll check for a "reference date" within the payroll period (midpoint)
        mid = date(self.run.year, self.run.month, min(15, (pend - pstart).days + 1))
        
        # If employee has any suspend-payroll situation covering the reference date → not eligible
        return not Situation.objects.filter(
            employee=emp,
            situation_type__suspend_payroll=True,
            start_date__lte=mid
        ).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=mid)).exists()

    def _active_contract(self, emp: Employee):
        pstart, pend, _ = self._period_bounds()
        qs = emp.contracts.filter(
            status="ACTIVE", start_date__lte=pend
        ).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=pstart))
        return qs.order_by("-start_date", "-id").first()

    def _prorate(self, amount: Decimal, emp: Employee) -> Decimal:
        if not amount:
            return Q("0.00")
        pstart, pend, total_days = self._period_bounds()

        # employee active window (hire/term)
        hire = getattr(emp, "hire_date", None) or pstart
        term = getattr(emp, "termination_date", None)
        active_start = max(pstart, hire)
        active_end = min(pend, term) if term else pend
        if active_end < active_start:
            return Q("0.00")

        if getattr(self.policy, "proration_method", "CALENDAR") == "WORKING":
            total = self._working_days_in(pstart, pend)
            part = self._working_days_in(active_start, active_end)
        else:
            total = total_days
            part = (active_end - active_start).days + 1

        if total <= 0:
            return q2(amount)
        return q2(Q(amount) * Q(part) / Q(total))

    def _fx_to_policy_currency(self, amount: Decimal, from_cur: Optional[Currency]) -> Decimal:
        if not amount:
            return Q("0.00")
        policy_cur = getattr(self.policy, "currency", None)
        if not from_cur or not policy_cur or from_cur == policy_cur:
            return q2(amount)

        _, pend, _ = self._period_bounds()
        rate = (ExchangeRate.objects
                .filter(base=from_cur, quote=policy_cur, date__lte=pend)
                .order_by("-date").first())
        if not rate:
            # fallback 1:1
            return q2(amount)
        return q2(Q(amount) * Q(rate.rate))

    def _get_basic_component(self) -> PayrollComponent:
        comp = PayrollComponent.objects.filter(code="BASIC").first()
        if comp:
            return comp
        comp = PayrollComponent.objects.filter(kind=PayrollComponent.EARNING).order_by("sequence", "id").first()
        if not comp:
            raise RuntimeError("No earning component configured (need BASIC).")
        return comp

    # -------------- collectors (lines) --------------

    def _collect_recurring(self, emp: Employee, base_for_pct: Decimal) -> list[PayslipItem]:
        """
        RecurringComponentAssignment active in period (amount or % of base).
        """
        pstart, pend, _ = self._period_bounds()
        rows = (RecurringComponentAssignment.objects
                .select_related("component")
                .filter(employee=emp, active=True, start_date__lte=pend)
                .filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=pstart))
                .order_by("component__sequence", "id"))

        items: list[PayslipItem] = []
        for r in rows:
            comp = r.component
            amt = Q(r.amount or 0)
            if (not amt) and r.percentage:
                amt = Q(base_for_pct) * Q(r.percentage)
            amt = q2(amt)
            if amt == 0:
                continue
            items.append(PayslipItem(
                component=comp, quantity=1, rate=amt, amount=amt,
                meta={"source": "recurring", "assignment_id": r.id}
            ))
        return items

    def _collect_variables(self, emp: Employee) -> list[PayslipItem]:
        """
        VariableInput for this run & employee:
          - Prefer rows explicitly linked to run
          - Also accept run=None created in the same period (optional convenience)
        """
        pstart, pend, _ = self._period_bounds()
        vi_qs = (VariableInput.objects
                 .select_related("component")
                 .filter(employee=emp)
                 .filter(models.Q(run=self.run) |
                         models.Q(run__isnull=True, created_at__date__gte=pstart, created_at__date__lte=pend))
                 .order_by("component__sequence", "id"))

        items: list[PayslipItem] = []
        for v in vi_qs:
            # prefer explicit amount; else qty * rate
            amt = Q(v.amount or 0)
            if not amt:
                amt = Q(v.quantity or 0) * Q(v.rate or 0)
            amt = q2(amt)
            if amt == 0:
                continue
            items.append(PayslipItem(
                component=v.component,
                quantity=v.quantity or 1,
                rate=q2(v.rate or amt),
                amount=amt,
                meta={"source": "variable", "variable_id": v.id, "note": v.note}
            ))
        return items

    # -------------- taxes & contributions --------------

    def _compute_tax(self, pit_base: Decimal) -> Decimal:
        table: Optional[TaxTable] = getattr(self.policy, "active_tax_table", None)
        if not table:
            return Q("0.00")
        base = max(Q("0.00"), Q(pit_base))
        tax = Q("0.00")
        for br in table.brackets.all().order_by("lower"):
            lower = Q(br.lower)
            upper = Q(br.upper) if br.upper is not None else None
            if base <= lower:
                break
            slab_top = upper if upper is not None else base
            slab = max(Q("0.00"), min(base, slab_top) - lower)
            tax += slab * Q(br.rate)
            if upper is None or base <= upper:
                break
        return q2(tax)

    def _apply_contributions(self, base: Decimal) -> tuple[Decimal, Decimal]:
        ee = Q("0.00"); er = Q("0.00")
        contribs = getattr(self.policy, "active_contribs", None)
        if not contribs:
            return ee, er
        for sch in contribs.all():
            b = Q(base)
            if getattr(sch, "cap", None):
                b = min(b, Q(sch.cap))
            ee += b * Q(sch.ee_rate or 0)
            er += b * Q(sch.er_rate or 0)
        return q2(ee), q2(er)

    # -------------- main compute --------------

    @transaction.atomic
    def compute_for_employee(self, emp: Employee) -> Optional[Payslip]:
        if not self._eligible(emp):
            return None

        # --- Contract base & FX to policy currency
        contract = self._active_contract(emp)
        raw_base = Q(getattr(contract, "salary", 0) or 0)
        emp_currency = getattr(contract, "currency", None) or getattr(emp, "currency", None)
        base_policy_ccy = self._fx_to_policy_currency(raw_base, emp_currency)
        base_prorated = self._prorate(base_policy_ccy, emp)

        slip, _ = Payslip.objects.get_or_create(
            run=self.run, employee=emp, defaults={"currency": self.policy.currency}
        )

        items: list[PayslipItem] = []

        # BASIC
        comp_basic = self._get_basic_component()
        items.append(PayslipItem(
            payslip=slip, component=comp_basic,
            quantity=1, rate=base_prorated, amount=base_prorated,
            meta={"source": "basic", "contract_id": getattr(contract, "id", None)}
        ))

        # Recurring (allowances/deductions)
        items += self._collect_recurring(emp, base_prorated)

        # Variable inputs (overtime, bonuses, one-offs)
        items += self._collect_variables(emp)

        # ---- Aggregate totals
        def is_kind(i, kind): return getattr(i.component, "kind", "") == kind
        def is_taxable(i):     return bool(getattr(i.component, "taxable", False))
        def is_contrib(i):     return bool(getattr(i.component, "contributory", False))

        gross_earnings = sum((i.amount for i in items if is_kind(i, PayrollComponent.EARNING)), Q("0.00"))
        employer_only  = sum((i.amount for i in items if is_kind(i, PayrollComponent.EMPLOYER)), Q("0.00"))  # not used in net

        # Deductions (treat all as post-tax unless component has pre_tax=True attribute)
        pre_tax_deds = sum((i.amount for i in items
                            if is_kind(i, PayrollComponent.DEDUCTION) and getattr(i.component, "pre_tax", False)), Q("0.00"))
        post_tax_deds = sum((i.amount for i in items
                             if is_kind(i, PayrollComponent.DEDUCTION) and not getattr(i.component, "pre_tax", False)), Q("0.00"))

        taxable_gross = sum((i.amount for i in items if is_kind(i, PayrollComponent.EARNING) and is_taxable(i)), Q("0.00"))
        contrib_base  = sum((i.amount for i in items if is_kind(i, PayrollComponent.EARNING) and is_contrib(i)), Q("0.00"))

        ee_contrib, er_contrib = self._apply_contributions(contrib_base)

        pit_base = max(Q("0.00"), taxable_gross - ee_contrib - pre_tax_deds)
        pit = self._compute_tax(pit_base)

        other_deductions = q2(pre_tax_deds + post_tax_deds)
        net = q2(gross_earnings - ee_contrib - pit - other_deductions)

        # ---- Persist slip
        slip.base_salary      = q2(base_prorated)
        slip.gross_pay        = q2(gross_earnings)
        slip.taxable_gross    = q2(taxable_gross)
        slip.employee_contrib = q2(ee_contrib)
        slip.employer_contrib = q2(er_contrib)
        slip.income_tax       = q2(pit)
        slip.other_deductions = q2(other_deductions)
        slip.net_pay          = q2(net)
        slip.currency         = self.policy.currency
        slip.finalized        = False
        slip.save()

        # Replace items
        PayslipItem.objects.filter(payslip=slip).delete()
        for i in items:
            i.payslip = slip
        PayslipItem.objects.bulk_create(items)

        return slip

    @transaction.atomic
    def compute_run(self, employee_ids: Optional[Iterable] = None) -> list[int]:
        pstart, pend, _ = self._period_bounds()

        qs = Employee.objects.filter(user__is_active=True).filter(
            contracts__status="ACTIVE", contracts__start_date__lte=pend
        ).filter(
            models.Q(contracts__end_date__isnull=True) | models.Q(contracts__end_date__gte=pstart)
        )

        # Narrow to employees under this policy if your Contract has FK to CompanyPolicy
        try:
            qs = qs.filter(contracts__company_policy=self.policy)
        except Exception:
            try:
                qs = qs.filter(company_policy=self.policy)
            except Exception:
                pass

        if employee_ids:
            qs = qs.filter(id__in=list(employee_ids))

        qs = qs.distinct().select_related("department", "grade")

        out: list[int] = []
        for emp in qs:
            slip = self.compute_for_employee(emp)
            if slip:
                out.append(slip.id)

        self.run.status = PayrollRun.PROCESSED
        self.run.processed_at = timezone.now()
        self.run.save(update_fields=["status", "processed_at"])
        return out


