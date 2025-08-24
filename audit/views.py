# audit/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Q
from auditlog.models import LogEntry
from .serializers import LogEntrySerializer, ContentTypeSlimSerializer
from .permissions import IsAdminOrAuditorOrStaff
from django.contrib.contenttypes.models import ContentType

class AuditPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEntry.objects.all().select_related("actor", "content_type")
    serializer_class = LogEntrySerializer
    pagination_class = AuditPagination
    permission_classes = [IsAuthenticated, IsAdminOrAuditorOrStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params

        if p.get("actor"):        qs = qs.filter(actor_id=p.get("actor"))
        if p.get("action"):       qs = qs.filter(action=p.get("action"))
        if p.get("content_type"): qs = qs.filter(content_type_id=p.get("content_type"))
        if p.get("object_pk"):    qs = qs.filter(object_pk=str(p.get("object_pk")))
        if p.get("date_from"):    qs = qs.filter(timestamp__date__gte=p.get("date_from"))
        if p.get("date_to"):      qs = qs.filter(timestamp__date__lte=p.get("date_to"))
        if p.get("q"):
            qs = qs.filter(
                Q(object_repr__icontains=p["q"]) |
                Q(changes_text__icontains=p["q"]) |
                Q(remote_addr__icontains=p["q"])
            )
        return qs

    def contenttypes(self, request):
        qs = ContentType.objects.all().order_by("app_label","model")
        return Response(ContentTypeSlimSerializer(qs, many=True).data)
    def actor_list(self, request):
        qs = LogEntry.objects.values("actor_id").distinct().order_by("actor__username")
        return Response([{"id": a["actor_id"], "username": a["actor__username"]} for a in qs])
    








