# notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, redirect
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from django.utils import timezone
from django.db.models import Q, F

class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all().order_by('-timestamp')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = super().get_queryset()
        # also include user=NULL but addressed to my email/phone
        emails = [u.email] if u.email else []
        phones = []
        emp = getattr(u, 'employee', None)
        if emp and getattr(emp, 'contact', None):
            phones.append(emp.contact)

        qs = qs.filter(Q(user=u) | Q(user__isnull=True, recipient__in=(emails+phones)))

        # filters
        p = self.request.query_params
        if 'is_read' in p:
            qs = qs.filter(is_read=(p.get('is_read') in ('1','true','True')))
        if 'status' in p:
            qs = qs.filter(status=p.get('status'))
        if 'category' in p:
            qs = qs.filter(category=p.get('category'))
        if 'channel' in p:
            qs = qs.filter(channel=p.get('channel'))
        return qs

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.mark_read()
        return Response({'ok': True, 'read_at': n.read_at})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(is_read=False)
        qs.update(is_read=True, status='read', read_at=timezone.now())
        return Response({'ok': True, 'updated': qs.count()})



class NotificationPreferenceViewSet(ModelViewSet):
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

def notification_center_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'notifications/notification_center.html')

