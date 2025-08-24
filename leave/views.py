# leave/views.py
from django.shortcuts import render, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from datetime import datetime
from .models import LeaveRequest, LeaveType, LeaveBalance
from .serializers import *
from employee.permissions import *
from employee.models import Employee
from django.utils.timezone import now
from .tasks import (
    notify_leave_request_submission,
    notify_leave_request_response,
    notify_leave_balance_update,
    notify_overlapping_leave,
    notify_delegate_leave,
)
from rest_framework.permissions import IsAuthenticated
from .permissions import CanEditDeleteOwnLeave  # New import

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee', 'leave_type').prefetch_related('document').order_by('-requested_at')
    serializer_class = LeaveRequestSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    # def get_permissions(self):
    #     if self.action in ['update', 'partial_update', 'destroy', 'approve', 'hr_approve']:
    #         return [CanEditDeleteOwnLeave()]
    #     elif self.action in ['approve', 'hr_approve']:
    #         return [IsAdminOrHR()]
    #     elif self.action == 'create':
    #         return [IsOwnProfile()]
    #     return [IsAuthenticated()]
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [CanEditDeleteOwnLeave()]
        # elif self.action in ['approve', 'hr_approve']:
        #     return [IsAdminOrHR()]
        elif self.action == 'approve':
            return [IsManager()]          # Manager does manager-approve
        elif self.action == 'hr_approve':
            return [IsAdminOrHR()]       # HR/Admin does HR-approve
        elif self.action == 'create':
            return [IsOwnProfile()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'MANAGER':
            # Managers only see requests from their subordinates
            queryset = queryset.filter(employee__manager=user.employee)
        elif user.role not in ['HR', 'ADMIN']:
            # Employees only see their own requests
            queryset = queryset.filter(employee=user.employee)
        # HR and ADMIN see all requests

        date_range = self.request.query_params.get('date_range', '')
        employee_id = self.request.query_params.get('employee_id', '')
        leave_type_id = self.request.query_params.get('leave_type_id', '')
        status = self.request.query_params.get('status', '')
        is_read = self.request.query_params.get('is_read', '')

        if date_range:
            try:
                start_date_str, end_date_str = date_range.split(' to ')
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # Overlap: start <= end && end >= start
                start_date <= end_date and end_date >= start_date
                queryset = queryset.filter(
                    Q(start_date__gte=start_date) & Q(end_date__lte=end_date)
                )
            except ValueError:
                pass
        if employee_id:
            queryset = queryset.filter(employee__id=employee_id)
        if leave_type_id:
            queryset = queryset.filter(leave_type__id=leave_type_id)
        if status:
            queryset = queryset.filter(status=status)
        if is_read in ['true', 'false']:
            queryset = queryset.filter(is_read=(is_read == 'true'))
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role in ['MANAGER', 'HR', 'ADMIN'] or request.user.employee == instance.employee:
            instance.is_read = True
            instance.save()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        leave = serializer.instance
        notify_leave_request_submission.delay(leave.id)
        notify_overlapping_leave.delay(leave.id)
        notify_delegate_leave.delay(leave.id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'MANAGER' and instance.employee.manager != request.user.employee:
            return Response({'error': 'You can only update requests from your subordinates'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        notify_leave_request_response.delay(instance.id)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], name='Approve by Manager')
    def approve(self, request, pk=None):
        leave = self.get_object()
        if request.user.role == 'MANAGER' and leave.employee.manager != request.user.employee:
            return Response({'error': 'You can only approve requests from your subordinates'}, status=status.HTTP_403_FORBIDDEN)
        leave.status = 'manager_approved'
        leave.approved_by = request.user
        leave.is_read = True
        leave.save()
        notify_leave_request_response.delay(leave.id)
        return Response({'status': 'manager_approved'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], name='Approve by HR')
    def hr_approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'manager_approved':
            return Response({'error': 'Manager approval required.'}, status=status.HTTP_400_BAD_REQUEST)
        leave.status = 'hr_approved'
        leave.is_read = True
        leave.save()
        year = leave.start_date.year
        working_days = leave.calculate_working_days()
        balance = LeaveBalance.objects.get(employee=leave.employee, leave_type=leave.leave_type, year=year)
        balance.balance -= working_days
        balance.save()
        notify_leave_request_response.delay(leave.id)
        notify_leave_balance_update.delay(
            employee_id=leave.employee.id,
            leave_type_id=leave.leave_type.id,
            year=year,
            new_balance=balance.balance
        )
        return Response({'status': 'hr_approved'}, status=status.HTTP_200_OK)

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all().order_by('name')
    serializer_class = LeaveTypeSerializer
    # permission_classes = [IsAdminOrHR]
    pagination_class = StandardResultsSetPagination
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrHR()]

def leave_create_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    context = {
        'leave_types': LeaveType.objects.all(),
        'employees': Employee.objects.all() if request.user.role in ['ADMIN', 'HR'] or request.user.is_staff else [request.user.employee]
    }
    if request.method == 'POST':
        data = request.POST.copy()
        data['employee'] = request.user.employee.id if request.user.role == 'EMP' else data['employee']
        serializer = LeaveRequestSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            leave = serializer.save()
            notify_leave_request_submission.delay(leave.id)
            notify_overlapping_leave.delay(leave.id)
            return redirect('leave_list')
        context['errors'] = serializer.errors
    return render(request, 'leave/leave_create.html', context)

def leave_list_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'leave/leave_list.html', {})

def leave_management_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role not in ['MANAGER', 'HR', 'ADMIN']:
        return redirect('leave_list')
    return render(request, 'leave/leave_management.html', {})


def my_leave_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'leave/my_leave.html', {})


# leave/views.py

from rest_framework.permissions import IsAuthenticated
from django.db.models import OuterRef

class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.select_related('leave_type').filter(employee__user=OuterRef('request.user')).order_by('year', 'leave_type__name')
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LeaveBalance.objects.filter(employee__user=self.request.user).select_related('leave_type').order_by('year', 'leave_type__name')

def my_leave_create_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    context = {
        'leave_types': LeaveType.objects.all()
    }
    return render(request, 'leave/my_leave_create.html', context)

def leave_calendar_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'leave/leave_calendar.html', {})
