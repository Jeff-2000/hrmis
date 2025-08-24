import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# class DocumentViewSet(viewsets.ModelViewSet):
#     queryset = Document.objects.all().order_by('-uploaded_at')
#     serializer_class = DocumentSerializer
#     pagination_class = StandardResultsSetPagination
#     parser_classes = [MultiPartParser, FormParser]
#     permission_classes = [IsAuthenticated]
#     http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

#     def get_queryset(self):
#         user = self.request.user
#         role = (getattr(user, 'role', '') or '').upper()

#         qs = super().get_queryset()

#         # ---- BASIC OWNERSHIP RULE ----
#         # EMP users only see documents attached to *their* Employee object.
#         if role not in ('HR', 'ADMIN'):
#             try:
#                 emp = user.employee
#             except Exception:
#                 emp = None
#             if not emp:
#                 return qs.none()
#             emp_ct = ContentType.objects.get(app_label='employee', model='employee')
#             qs = qs.filter(content_type=emp_ct, object_id=emp.id)

#         # ---- FILTERS ----
#         params = self.request.query_params
#         doc_type   = params.get('document_type')
#         status_f   = params.get('status')
#         ct_id      = params.get('content_type')   # int id
#         obj_id     = params.get('object_id')      # numeric
#         q          = params.get('q')
#         year_from  = params.get('year_from')
#         year_to    = params.get('year_to')

#         if doc_type:
#             qs = qs.filter(document_type=doc_type)
#         if status_f:
#             qs = qs.filter(status=status_f)
#         if ct_id:
#             qs = qs.filter(content_type_id=ct_id)
#         if obj_id:
#             qs = qs.filter(object_id=obj_id)
#         if q:
#             qs = qs.filter(Q(issued_by__icontains=q) | Q(content_text__icontains=q))
#         if year_from:
#             qs = qs.filter(issuance_date__year__gte=year_from)
#         if year_to:
#             qs = qs.filter(issuance_date__year__lte=year_to)

#         return qs

#     def perform_create(self, serializer):
#         """
#         EMP: force documents to attach to their own Employee object (ignore arbitrary content targets)
#         HR/ADMIN: can set any content_type/object_id from the UI
#         """
#         user = self.request.user
#         role = (getattr(user, 'role', '') or '').upper()

#         if role in ('HR', 'ADMIN'):
#             serializer.save()
#         else:
#             # Force attach to current employee
#             emp = getattr(user, 'employee', None)
#             if not emp:
#                 raise PermissionError("Employee not found for current user.")
#             emp_ct = ContentType.objects.get(app_label='employee', model='employee')
#             serializer.save(content_type=emp_ct, object_id=emp.id)

#     def perform_update(self, serializer):
#         """EMP can only edit their own docs (already filtered by queryset). HR/ADMIN can edit all."""
#         serializer.save()
#         logger.info(f"Document updated successfully: {serializer.data}")

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination
    
    

# documents/views.py
import logging
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.apps import apps

from .models import Document
from .serializers import DocumentSerializer

from authentication.models import User  # adjust if your user model is elsewhere
from employee.models import Employee    # used for content type & PK probe

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def _mine_q(self, request):
        """
        Documents that belong to the logged-in user, directly or via objects
        tied to their employee (Contract, Payslip, Situation).
        Works even if Employee PK is UUID (we only use integer child-object IDs).
        """
        u = request.user
        q = Q()

        # 1) Directly attached to the User row
        try:
            ct_user = ContentType.objects.get_for_model(User)
            q |= Q(content_type=ct_user, object_id=int(u.id))
        except (TypeError, ValueError):
            pass  # custom UUID user IDs would be incompatible with int object_id

        # 2) Attached to the Employee row (only if employee PK is numeric)
        emp = getattr(u, 'employee', None)
        ct_emp = ContentType.objects.get_for_model(Employee)
        if emp is not None:
            try:
                emp_pk_int = int(getattr(emp, 'pk', emp.id))
                q |= Q(content_type=ct_emp, object_id=emp_pk_int)
            except (TypeError, ValueError):
                # UUID employee: skip direct Employee attachment
                pass

        # 3) Attached to child objects that reference this employee
        #    Contract, Payslip, Situation (extend as needed)
        MODEL_MAP = [
            ('payroll', 'Contract'),
            ('payroll', 'Payslip'),
            ('situation', 'Situation'),
        ]
        for app_label, model_name in MODEL_MAP:
            Model = apps.get_model(app_label, model_name)
            if Model is None:
                continue
            # Must be models with integer primary keys
            if emp is None:
                continue
            try:
                ids = list(
                    Model.objects.filter(employee=emp).values_list('id', flat=True)
                )
                if ids:
                    ct = ContentType.objects.get_for_model(Model)
                    q |= Q(content_type=ct, object_id__in=ids)
            except Exception:
                # model missing 'employee' FK or other mismatch — just skip safely
                continue

        return q

    def get_queryset(self):
        qs = super().get_queryset()
        req = self.request
        user = req.user
        role = (getattr(user, 'role', '') or '').upper()

        # --- quick param parsing ---
        params = req.query_params
        mine = params.get('mine')
        content_type = params.get('content_type')
        object_id = params.get('object_id')
        document_type = params.get('document_type')
        status_f = params.get('status')
        year_from = params.get('year_from')
        year_to = params.get('year_to')
        q_text = params.get('q')

        # --- visibility guard ---
        # EMP sees only "mine" by default, unless explicitly filtered and role is HR/ADMIN
        if role not in ('HR', 'ADMIN'):
            qs = qs.filter(self._mine_q(req))
        else:
            # HR/ADMIN can optionally use ?mine=1 to see their own only
            if mine in ('1', 'true', 'yes'):
                qs = qs.filter(self._mine_q(req))

        # --- filters (robust) ---
        if content_type:
            try:
                qs = qs.filter(content_type_id=int(content_type))
            except (TypeError, ValueError):
                # ignore invalid content_type
                pass

        if object_id:
            # Only apply if numeric, since Document.object_id is int
            try:
                qs = qs.filter(object_id=int(object_id))
            except (TypeError, ValueError):
                # ignore non-numeric object_id instead of raising
                logger.warning("Ignored non-numeric object_id=%r on documents list", object_id)

        if document_type:
            qs = qs.filter(document_type=document_type)

        if status_f:
            qs = qs.filter(status=status_f)

        if year_from:
            try:
                qs = qs.filter(issuance_date__year__gte=int(year_from))
            except (TypeError, ValueError):
                pass

        if year_to:
            try:
                qs = qs.filter(issuance_date__year__lte=int(year_to))
            except (TypeError, ValueError):
                pass

        if q_text:
            qs = qs.filter(Q(issued_by__icontains=q_text) | Q(content_text__icontains=q_text))

        return qs

    def create(self, request, *args, **kwargs):
        logger.info(f"POST /api/v1/documents/ data={request.data}")
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error("Error creating document: %s", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # extra safety: only allow editing/deleting "to_validate" for non HR/ADMIN
    def _ensure_editable_by_user(self, instance):
        user = self.request.user
        role = (getattr(user, 'role','') or '').upper()
        if role in ('HR','ADMIN'):
            return
        if instance.status != 'to_validate':
            raise PermissionDenied("Vous ne pouvez modifier ou supprimer que les documents 'À valider'.")

        # also ensure it's part of mine
        mine_q = self._mine_q(self.request)
        if not Document.objects.filter(Q(pk=instance.pk) & mine_q).exists():
            raise PermissionDenied("Accès refusé.")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_editable_by_user(instance)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_editable_by_user(instance)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_editable_by_user(instance)
        return super().destroy(request, *args, **kwargs)






