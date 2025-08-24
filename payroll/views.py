# payroll/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import PayrollRecord
from .serializers import PayrollRecordSerializer
from employee.permissions import IsAdminOrHR
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
import csv
from django.shortcuts import render, get_object_or_404

# # To delete
# class PayrollRecordViewSet(viewsets.ModelViewSet):
#     queryset = PayrollRecord.objects.select_related('employee').all()
#     serializer_class = PayrollRecordSerializer
#     permission_classes = [IsAuthenticated]

#     def get_permissions(self):
#         # Only HR/finance (assume HR role) can modify payroll records
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsAdminOrHR()]
#         return [IsAuthenticated()]
    
#     def perform_create(self, serializer):
#         # Compute net_salary before saving (base + allowances - deductions)
#         base = serializer.validated_data['base_salary']
#         allowances = serializer.validated_data.get('allowances', 0)
#         deductions = serializer.validated_data.get('deductions', 0)
#         net = base + allowances - deductions
#         serializer.save(net_salary=net)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from .models import SituationType, Payroll
from .serializers import *
from employee.models import Employee
from situation.models import Situation
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.http import Http404
from django.forms.models import model_to_dict
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payroll.permissions import IsSelfOrHR

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SituationTypeViewSet(viewsets.ModelViewSet):
    queryset = SituationType.objects.all().order_by('name')
    serializer_class = SituationTypeSerializer
    pagination_class = StandardResultsSetPagination
    # permission_classes = [IsAdminOrHR] 
    permission_classes = [IsAuthenticated]

class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.select_related('employee').all().order_by('-year', '-month')
    serializer_class = PayrollSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAdminOrHR]

    @action(detail=False, methods=['post'], name='Generate payroll for month')
    def generate(self, request):
        month = int(request.data.get('month', timezone.now().month))
        year = int(request.data.get('year', timezone.now().year))

        # Identify employees with payroll-suspending situations
        # excluded_ids = AdministrativeSituation.objects.filter(
        #     Q(situation_type__suspend_payroll=True) &
        #     Q(start_date__lte=timezone.now().date()) &
        #     (Q(end_date__gte=timezone.now().date()) | Q(end_date__isnull=True))
        # ).values_list('employee_id', flat=True)
        excluded_ids = Situation.objects.filter(
            Q(situation_type__suspend_payroll=True) &
            Q(start_date__lte=timezone.now().date()) &
            (Q(end_date__gte=timezone.now().date()) | Q(end_date__isnull=True))
        ).values_list('employee_id', flat=True)

        employees = Employee.objects.filter(is_active=True).exclude(id__in=excluded_ids)
        created_records = []

        for emp in employees:
            base_salary = getattr(emp, 'base_salary', 0)  # Assume Employee has base_salary
            allowances = 0  # Add logic for allowances if needed
            deductions = 0  # Add logic for deductions if needed

            payroll_obj, created = Payroll.objects.update_or_create(
                employee=emp, year=year, month=month,
                defaults={
                    'base_salary': base_salary,
                    'allowances': allowances,
                    'deductions': deductions,
                    'status': 'pending',
                }
            )
            created_records.append(PayrollSerializer(payroll_obj).data)

        return Response(created_records, status=status.HTTP_200_OK)


# payroll/views.py (extend / replace where appropriate)

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
import csv, io, hashlib
from payroll.models import *
from payroll.serializers import *
from .permissions import *
from payroll.services.engines import PayrollEngine
from django.shortcuts import get_object_or_404
from . tasks import *

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10; page_size_query_param = 'page_size'; max_page_size = 100

class SituationTypeViewSet(viewsets.ModelViewSet):
    queryset = SituationType.objects.all().order_by('name')
    serializer_class = SituationTypeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAdminOrHR]

class PayrollComponentViewSet(viewsets.ModelViewSet):
    queryset = PayrollComponent.objects.all().order_by('sequence', 'code')
    serializer_class = PayrollComponentSerializer
    permission_classes = [IsAdminOrHR]

class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.select_related('company_policy').all().order_by('-year','-month')
    serializer_class = PayrollRunSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAdminOrHR]
    
    @action(detail=True, methods=['post'], url_path="generate", permission_classes=[IsAuthenticated, IsAdminOrHR])
    def generate(self, request, pk=None):
        """
        (Re)compute the run: idempotent while run is DRAFT. Sets status=processed.
        """
        run = self.get_object()
        if run.status == PayrollRun.CLOSED:
            return Response({'detail': 'Run is closed.'}, status=400)
        engine = PayrollEngine(run)
        ids = engine.compute_run()
        
        # Notify actor + employees (payslip ready)
        try:
            notify_run_generated.delay(run.id, request.user.id, len(ids))
            notify_employees_payslips_ready.delay(run.id)
        except Exception:
            notify_run_generated(run.id, request.user.id, len(ids))
            notify_employees_payslips_ready(run.id)

        return Response({"detail": "Run processed", "payslip_ids": ids})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrHR])
    def close(self, request, pk=None):
        run = self.get_object()
        if run.status != PayrollRun.PROCESSED:
            return Response({'detail': 'Run must be processed before closing.'}, status=400)
        run.status = PayrollRun.CLOSED
        run.closed_at = timezone.now()
        run.save(update_fields=['status','closed_at'])

        # Notify actor + employees (payment)
        try:
            notify_run_closed.delay(run.id, request.user.id)
        except Exception:
            notify_run_closed(run.id, request.user.id)

        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrHR])
    def reopen(self, request, pk=None):
        run = self.get_object()
        if run.status != PayrollRun.CLOSED:
            return Response({'detail': 'Only closed runs can be reopened to DRAFT.'}, status=400)
        run.status = PayrollRun.DRAFT
        run.closed_at = None
        run.processed_at = None
        run.save(update_fields=['status','closed_at','processed_at'])
        # (optional) delete payslips so it can be recomputed fresh
        run.payslips.all().delete()

        # Notify actor only
        try:
            notify_run_reopened.delay(run.id, request.user.id)
        except Exception:
            notify_run_reopened(run.id, request.user.id)
            
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        run = self.get_object()
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="payslips_{run.year}_{run.month}.csv"'
        w = csv.writer(resp)
        w.writerow(['Employee','Gross','Taxable','EE Contrib','ER Contrib','Tax','Other Deds','Net'])
        for p in run.payslips.select_related('employee'):
            full = f"{p.employee.first_name} {p.employee.last_name}"
            w.writerow([full, p.gross_pay, p.taxable_gross, p.employee_contrib, p.employer_contrib, p.income_tax, p.other_deductions, p.net_pay])
        return resp


class PayslipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payslip.objects.select_related('run','employee').all()
    serializer_class = PayslipSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsSelfOrHR]

    def _current_employee_id(self, request):
        emp = getattr(request.user, 'employee', None)
        return getattr(emp, 'id', None)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = (getattr(user, 'role', '') or '').upper()

        # Optional explicit filter: ?employee=<id|me>
        emp_param = self.request.query_params.get('employee')

        if role not in ('HR','ADMIN'):
            # Non-HR users are ALWAYS restricted to themselves
            me_id = self._current_employee_id(self.request)
            if not me_id:
                return qs.none()
            qs = qs.filter(employee_id=me_id)
        else:
            # HR/ADMIN: if employee filter provided, honor it (including "me")
            if emp_param:
                if emp_param == 'me':
                    me_id = self._current_employee_id(self.request)
                    if not me_id:
                        qs = qs.none()
                    else:
                        qs = qs.filter(employee_id=me_id)
                else:
                    qs = qs.filter(employee_id=emp_param)

        # Existing filters
        run_id = self.request.query_params.get('run')
        if run_id: qs = qs.filter(run_id=run_id)
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        if year: qs = qs.filter(run__year=year)
        if month: qs = qs.filter(run__month=month)
        return qs

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Always return payslips for the *current* user's employee,
        regardless of HR/ADMIN role.
        """
        me_id = self._current_employee_id(request)
        if not me_id:
            # If the logged-in user isn't linked to an Employee
            return self.get_paginated_response([]) if hasattr(self, 'paginator') else Response([])

        qs = super().get_queryset().filter(employee_id=me_id)

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)

        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """
        Render a printable PDF payslip. Uses WeasyPrint.
        """
        payslip = self.get_object()  # triggers object-level permission (IsSelfOrHR)
        try:
            from weasyprint import HTML
        except ImportError:
            return Response(
                {'detail': 'WeasyPrint is not installed. pip install weasyprint'},
                status=501
            )

        context = {
            'p': payslip,
            'employee': payslip.employee,
            'run': payslip.run,
            'items': payslip.items.select_related('component').all(),
            'company': getattr(payslip.run, 'company_policy', None),
            'request': request,  # for absolute URLs if needed
        }
        html = render_to_string('payroll/payslip_pdf.html', context)
        pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()

        fname = f"payslip_{payslip.employee.last_name}_{payslip.run.month}_{payslip.run.year}.pdf".replace(' ', '_')
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        # inline lets it open in a new tab; change to attachment to force download
        resp['Content-Disposition'] = f'inline; filename="{fname}"'
        return resp

    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """
        Export all payslips of this run as CSV.
        Columns: Employee, Matricule, Dept, Grade, Gross, Taxable, EE Contrib, ER Contrib, Tax, Other Deds, Net, Currency, Finalized, Created
        """
        run = self.get_object()

        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="payslips_{run.year}_{str(run.month).zfill(2)}.csv"'
        w = csv.writer(resp)

        w.writerow([
            'Employee', 'Matricule', 'Department', 'Grade',
            'Gross', 'Taxable Gross', 'EE Contrib', 'ER Contrib',
            'Income Tax', 'Other Deductions', 'Net Pay',
            'Currency', 'Finalized', 'Created At'
        ])

        qs = run.payslips.select_related('employee', 'employee__department', 'employee__grade', 'currency').all()
        for p in qs:
            emp = p.employee
            w.writerow([
                f"{emp.first_name} {emp.last_name}",
                getattr(emp, 'matricule', '') or '',
                getattr(getattr(emp, 'department', None), 'name', '') or '',
                getattr(getattr(emp, 'grade', None), 'name', '') or '',
                p.gross_pay, p.taxable_gross, p.employee_contrib, p.employer_contrib,
                p.income_tax, p.other_deductions, p.net_pay,
                getattr(p.currency, 'code', '') or '',
                'YES' if p.finalized else 'NO',
                p.created_at.strftime('%Y-%m-%d %H:%M'),
            ])

        return resp


class CompanyPolicyViewSet(viewsets.ModelViewSet):
    queryset = CompanyPolicy.objects.select_related('currency','active_tax_table').prefetch_related('active_contribs').all()
    serializer_class = CompanyPolicySerializer
    permission_classes = [IsAdminOrHR]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['country']

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all().order_by('code')
    serializer_class = CurrencySerializer
    permission_classes = [IsAdminOrHR]

class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.select_related('base','quote').all().order_by('-date')
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAdminOrHR]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['base', 'quote', 'date']

class TaxTableViewSet(viewsets.ModelViewSet):
    queryset = TaxTable.objects.all()
    serializer_class = TaxTableSerializer
    permission_classes = [IsAdminOrHR]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['country']

class TaxBracketViewSet(viewsets.ModelViewSet):
    queryset = TaxBracket.objects.select_related('table').all().order_by('lower')
    serializer_class = TaxBracketSerializer
    permission_classes = [IsAdminOrHR]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['table']

class ContributionSchemeViewSet(viewsets.ModelViewSet):
    queryset = ContributionScheme.objects.all().order_by('-valid_from')
    serializer_class = ContributionSchemeSerializer
    permission_classes = [IsAdminOrHR]


class VariableInputViewSet(viewsets.ModelViewSet):
    queryset = VariableInput.objects.select_related('employee', 'component', 'run').all()
    serializer_class = VariableInputSerializer
    permission_classes = [IsAdminOrHR]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = super().get_queryset()
        run_id = self.request.query_params.get('run')
        emp_id = self.request.query_params.get('employee')
        if run_id: qs = qs.filter(run_id=run_id)
        if emp_id: qs = qs.filter(employee_id=emp_id)
        return qs

    @action(detail=False, methods=['post'])
    def bulk_upsert(self, request):
        """
        Upsert a batch of variable inputs for a given run.
        Payload: { run_id, rows:[{employee_id, component_id, quantity, rate, amount, note}] }
        """
        run_id = request.data.get('run_id')
        rows = request.data.get('rows', [])
        if not run_id: return Response({'detail':'run_id is required'}, status=400)
        run = get_object_or_404(PayrollRun, pk=run_id)
        created = []
        for r in rows:
            ser = self.get_serializer(data={**r, 'run_id': run.id})
            ser.is_valid(raise_exception=True)
            obj = ser.save()
            created.append(self.get_serializer(obj).data)
        return Response({'created': created})

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        CSV columns: employee_id,component_code,quantity,rate,amount,note,run_id
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'detail':'file is required'}, status=400)
        import csv, codecs
        reader = csv.DictReader(codecs.iterdecode(file, 'utf-8'))
        out = []
        for row in reader:
            try:
                emp_id = int(row.get('employee_id'))
                comp = PayrollComponent.objects.get(code=row.get('component_code'))
                run_id = row.get('run_id') or None
                payload = {
                    'employee_id': emp_id, 'component_id': comp.id,
                    'quantity': row.get('quantity') or 1,
                    'rate': row.get('rate') or 0,
                    'amount': row.get('amount') or 0,
                    'note': row.get('note') or '',
                }
                if run_id:
                    payload['run_id'] = int(run_id)
                ser = self.get_serializer(data=payload)
                ser.is_valid(raise_exception=True)
                obj = ser.save()
                out.append(self.get_serializer(obj).data)
            except Exception as e:
                out.append({'error': str(e), 'row': row})
        return Response({'rows': out})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        qs = self.get_queryset()
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="variable_inputs.csv"'
        w = csv.writer(resp)
        w.writerow(['run_id','employee_id','component_code','quantity','rate','amount','note','created_at'])
        for v in qs.select_related('component'):
            w.writerow([v.run_id or '', v.employee_id, v.component.code, v.quantity, v.rate, v.amount, v.note, v.created_at.isoformat()])
        return resp


class RecurringComponentAssignmentViewSet(viewsets.ModelViewSet):
    queryset = RecurringComponentAssignment.objects.select_related('employee', 'component').all()
    serializer_class = RecurringComponentAssignmentSerializer
    permission_classes = [IsAdminOrHR]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = super().get_queryset()
        emp_id = self.request.query_params.get('employee')
        if emp_id: qs = qs.filter(employee_id=emp_id)
        return qs

class ContractViewSet(viewsets.ModelViewSet):
    # queryset = Contract.objects.select_related('employee').all()
    queryset = Contract.objects.select_related('employee','employee__department','employee__grade').all()
    serializer_class = ContractSerializer
    permission_classes = [IsAdminOrHR, HRAdminWriteSelfReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['employee__first_name','employee__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = (getattr(user, 'role', '') or '').upper()
        # allow everyone to filter by employee=... ; restrict non HR/ADMIN to themselves
        emp = self.request.query_params.get('employee')
        if emp:
            qs = qs.filter(employee_id=emp) | qs.filter(employee__pk=emp)
        if role not in ('HR','ADMIN'):
            if getattr(user, 'employee', None):
                qs = qs.filter(employee=user.employee)
            else:
                qs = qs.none()
        # optional extra filters
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status.upper())
        return qs



# Optional: your recurring model name; adapt if yours differs
try:
    HAS_RECURRING = True
except Exception:
    RecurringComponentAssignment = None
    HAS_RECURRING = False




# payroll/views_compensation.py


from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied




class CompensationViewSet(viewsets.ViewSet):
    """
    Read-only, computed resource.

    Routes:
      GET /api/v1/compensation/<employee_id>/
      GET /api/v1/compensation/?employee=<employee_id|me>

    <employee_id> may be:
      - "me"
      - integer PK
      - UUID PK (if Employee.pk is uuid)
      - 'uuid' field value (if your model has a separate uuid field)
    """
    permission_classes = [IsAuthenticated]

    # ---------- helpers ----------

    def _resolve_employee(self, request, emp_param: str) -> Employee:
        # "me"
        if emp_param == "me":
            emp = getattr(request.user, "employee", None)
            if not emp:
                raise Http404("Employee not found for current user.")
            return emp

        qs = Employee.objects.select_related("grade", "department")

        # int PK
        try:
            emp = qs.filter(pk=int(emp_param)).first()
            if emp:
                return emp
        except (ValueError, TypeError):
            pass

        # UUID PK (or string PK)
        emp = qs.filter(pk=emp_param).first()
        if emp:
            return emp

        # explicit uuid field
        if hasattr(Employee, "uuid"):
            emp = qs.filter(uuid=emp_param).first()
            if emp:
                return emp

        raise Http404("Employee not found.")

    def _authorize(self, request, employee: Employee):
        role = (getattr(request.user, "role", "") or "").upper()
        if role in ("HR", "ADMIN"):
            return
        me_emp_id = getattr(getattr(request.user, "employee", None), "id", None)
        if employee.id != me_emp_id:
            raise PermissionDenied("Vous n'avez pas l'autorisation pour ce profil.")

    def _emp_payload(self, e: Employee) -> dict:
        return {
            "id": e.pk,
            "matricule": getattr(e, "matricule", None),
            "first_name": getattr(e, "first_name", ""),
            "last_name": getattr(e, "last_name", ""),
            "full_name": f"{getattr(e, 'first_name','')} {getattr(e,'last_name','')}".strip(),
            "grade": {
                "id": getattr(getattr(e, "grade", None), "id", None),
                "name": getattr(getattr(e, "grade", None), "name", None),
            },
            "department": {
                "id": getattr(getattr(e, "department", None), "id", None),
                "name": getattr(getattr(e, "department", None), "name", None),
            },
            "status": getattr(e, "status", None),
            "is_active": getattr(e, "is_active", True),
        }

    def _contract_payload(self, c: Contract) -> dict:
        return {
            "id": c.id,
            "contract_type": c.contract_type,
            "salary": str(c.salary),
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "status": c.status,
            "notes": c.notes or "",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "is_active": c.is_active(),
        }

    def _recurring_payload(self, r) -> dict:
        comp = getattr(r, "component", None)
        return {
            "id": r.id,
            "component": {
                "id": getattr(comp, "id", None),
                "code": getattr(comp, "code", None),
                "name": getattr(comp, "name", None),
                "kind": getattr(comp, "kind", None),
            },
            "amount": str(getattr(r, "amount", Decimal("0.00"))),
            "percentage": str(getattr(r, "percentage", "")) if getattr(r, "percentage", None) is not None else None,
            "start_date": getattr(r, "start_date", None).isoformat() if getattr(r, "start_date", None) else None,
            "end_date": getattr(r, "end_date", None).isoformat() if getattr(r, "end_date", None) else None,
            "active": getattr(r, "active", True),
            "note": getattr(r, "note", "") or "",
        }

    def _payslip_payload(self, p: Payslip) -> dict:
        run = getattr(p, "run", None)
        return {
            "id": p.id,
            "run": {
                "id": getattr(run, "id", None),
                "year": getattr(run, "year", None),
                "month": getattr(run, "month", None),
                "status": getattr(run, "status", None),
            },
            "gross_pay": str(p.gross_pay),
            "net_pay": str(p.net_pay),
            "finalized": bool(p.finalized),
            "currency": getattr(getattr(p, "currency", None), "code", None),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    def _payload_for(self, employee: Employee) -> dict:
        contracts_qs = Contract.objects.filter(employee=employee).order_by("-start_date")
        if HAS_RECURRING:
            recurring_qs = (RecurringComponentAssignment.objects
                            .select_related("component")
                            .filter(employee=employee)
                            .order_by("-start_date", "id"))
        else:
            recurring_qs = []

        payslips_qs = (Payslip.objects
                       .select_related("run", "currency")
                       .filter(employee=employee)
                       .order_by("-run__year", "-run__month", "-id")[:12])

        return {
            "employee": self._emp_payload(employee),
            "contracts": [self._contract_payload(c) for c in contracts_qs],
            "recurring": [self._recurring_payload(r) for r in recurring_qs] if HAS_RECURRING else [],
            "payslips_recent": [self._payslip_payload(p) for p in payslips_qs],
        }

    # ---------- actions ----------

    def retrieve(self, request, pk=None):
        emp = self._resolve_employee(request, pk or "me")
        self._authorize(request, emp)
        return Response(self._payload_for(emp))

    def list(self, request):
        """
        GET /compensation/?employee=<id|me>
        (Keeps semantics explicit; avoids dumping all employees.)
        """
        emp_param = request.query_params.get("employee", None)
        if not emp_param:
            return Response({"detail": "Provide ?employee=<id|me>."}, status=status.HTTP_400_BAD_REQUEST)
        emp = self._resolve_employee(request, emp_param)
        self._authorize(request, emp)
        return Response(self._payload_for(emp))














