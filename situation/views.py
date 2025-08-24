from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from .models import Situation
from .serializers import SituationSerializer
from rest_framework.permissions import IsAuthenticated
from employee.permissions import IsAdminOrHR, IsOwnProfile
from .permissions import CanEditDeleteOwnSituation
from django.shortcuts import render

# situation/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from django.utils.encoding import smart_str
import csv
import os

from .models import Situation
from .serializers import SituationSerializer
from employee.permissions import IsAdminOrHR, IsOwnProfile
from .permissions import CanEditDeleteOwnSituation
from django.shortcuts import render

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SituationViewSet(viewsets.ModelViewSet):
    queryset = Situation.objects.select_related('employee', 'situation_type', 'document').all().order_by('-start_date')
    serializer_class = SituationSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        role = (getattr(self.request.user, 'role', '') or '').upper()
        if self.action in ['update', 'partial_update', 'destroy']:
            # HR/ADMIN can still do everything; employees go through the object-level CanEditDeleteOwnSituation
            if role in ('HR', 'ADMIN'):
                return [IsAuthenticated()]
            return [IsAuthenticated(), CanEditDeleteOwnSituation()]
        elif self.action in ['create', 'attach_document', 'close', 'reopen']:
            if role in ('EMP', 'HR', 'ADMIN'):
                return [IsAuthenticated()]
            # creation allowed for self only
            return [IsAuthenticated(), IsOwnProfile()]
        elif self.action in ['export_csv']:
            return [IsAuthenticated(), IsAdminOrHR()]
        return [IsAuthenticated()]

    def _parse_date_range(self, dr: str):
        try:
            s, e = dr.split(' to ')
            return timezone.datetime.strptime(s, '%Y-%m-%d').date(), timezone.datetime.strptime(e, '%Y-%m-%d').date()
        except Exception:
            return None, None

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = (getattr(user, 'role', '') or '').upper()

        # visibility
        if role == 'MANAGER':
            qs = qs.filter(employee__manager=user.employee)
        elif role not in ('HR', 'ADMIN'):
            qs = qs.filter(employee=user.employee)

        # filters
        params = self.request.query_params
        active = params.get('active')
        if active is not None:
            active = active.lower() in ('true', '1', 'yes')
            today = timezone.now().date()
            if active:
                qs = qs.filter(Q(end_date__gte=today) | Q(end_date__isnull=True), start_date__lte=today)
            else:
                qs = qs.exclude(Q(end_date__gte=today) | Q(end_date__isnull=True), start_date__lte=today)

        status_f = params.get('status')
        if status_f:
            qs = qs.filter(status__iexact=status_f)

        employee_id = params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        stype_id = params.get('situation_type_id')
        if stype_id:
            qs = qs.filter(situation_type_id=stype_id)

        type_code = params.get('type_code')
        if type_code:
            qs = qs.filter(situation_type__code__iexact=type_code)

        date_range = params.get('date_range')
        if date_range:
            s, e = self._parse_date_range(date_range)
            if s and e:
                # overlap: (start <= e) and (end is null or end >= s)
                qs = qs.filter(start_date__lte=e).filter(Q(end_date__isnull=True) | Q(end_date__gte=s))

        search = params.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(situation_type__name__icontains=search) |
                Q(situation_type__code__icontains=search)
            )

        ordering = params.get('ordering')
        allowed = {'start_date', '-start_date', 'end_date', '-end_date', 'status', 'situation_type__name', '-situation_type__name'}
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs

    # ---- Custom actions ----

    @action(detail=True, methods=['post'])
    def attach_document(self, request, pk=None):
        """
        Attach/replace a document by passing `document_id` (already created via /api/v1/documents/).
        """
        instance = self.get_object()
        doc_id = request.data.get('document_id')
        if not doc_id:
            return Response({'detail': 'document_id is required.'}, status=400)
        from documents.models import Document
        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'detail': 'Document not found.'}, status=404)
        instance.document = doc
        instance.save(update_fields=['document'])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """
        Mark situation as finished (status='terminé').
        Optionally accept `end_date` (defaults to today) and `resumption_date`.
        """
        instance = self.get_object()
        today = timezone.localdate()
        end_date = request.data.get('end_date')
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            except Exception:
                return Response({'detail': 'Invalid end_date.'}, status=400)
        else:
            end_date = today
        instance.end_date = end_date
        instance.status = 'terminé'
        resumption = request.data.get('resumption_date')
        if resumption:
            try:
                instance.resumption_date = timezone.datetime.strptime(resumption, '%Y-%m-%d').date()
            except Exception:
                return Response({'detail': 'Invalid resumption_date.'}, status=400)
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """
        Reopen a finished situation: clears end_date and sets status to 'actif'.
        """
        instance = self.get_object()
        instance.end_date = None
        instance.status = 'actif'
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        CSV export of the filtered queryset (HR/ADMIN only).
        Reuses get_queryset() filters.
        """
        qs = self.get_queryset()
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="situations.csv"'
        writer = csv.writer(resp)
        writer.writerow([
            'Employé', 'Type', 'Code', 'Début', 'Fin', 'Statut',
            'Suspend paie', 'Document', 'Document URL', 'Disponibilité', 'Exclusion', 'Sortie'
        ])
        for s in qs:
            # Combine first_name and last_name
            full_name = f"{s.employee.first_name} {s.employee.last_name}"
            
            doc_name = ''
            doc_url = ''
            doc = getattr(s, 'document', None)
            
            if doc:
                # Name/label
                doc_name = getattr(doc, 'original_name', '') or getattr(doc, 'filename', '')
                if not doc_name and getattr(doc, 'file', None):
                    try:
                        doc_name = os.path.basename(doc.file.name or '')
                    except Exception:
                        doc_name = ''
                # URL
                try:
                    if getattr(doc, 'file', None) and hasattr(doc.file, 'url'):
                        doc_url = request.build_absolute_uri(doc.file.url)
                    elif getattr(doc, 'url', None):
                        doc_url = request.build_absolute_uri(doc.url)
                except Exception:
                    doc_url = ''
            
            writer.writerow([
                smart_str(full_name),
                smart_str(s.situation_type.name),
                smart_str(s.situation_type.code),
                s.start_date.isoformat(),
                s.end_date.isoformat() if s.end_date else '',
                smart_str(s.status),
                'Oui' if getattr(s.situation_type, 'suspend_payroll', False) else 'Non',
                # smart_str(getattr(s.document, 'original_name', '') or getattr(s.document, 'filename', '') or ''),
                smart_str(doc_name),
                smart_str(doc_url),
                smart_str(s.availability_reason or ''),
                smart_str(s.exclusion_reason or ''),
                smart_str(s.exit_type or ''),
            ])
        return resp

# Simple views for the pages
def situation_current(request):
    return render(request, 'situation/current.html')

def situation_history(request):
    return render(request, 'situation/history.html')

def my_situation(request):
    return render(request, 'situation/my_situation.html')





