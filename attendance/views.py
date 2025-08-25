# attendance/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from .models import AttendanceRecord
from django.conf import settings
from .serializers import AttendanceRecordSerializer
from employee.models import *
from attendance.permissions import IsAdminHrManagerAndOnSite
from employee.permissions import IsAdminOrHRorStaff
import datetime
import logging
import calendar 

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse, Http404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser

import json


logger = logging.getLogger(__name__)

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('employee').all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'summary']:
            return [IsAdminOrHRorStaff(), IsAdminHrManagerAndOnSite()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Apply filters
        date_range = self.request.query_params.get('date_range', '')
        employee_id = self.request.query_params.get('employee_id', '')
        department_id = self.request.query_params.get('department_id', '')
        status = self.request.query_params.get('status', '')

        date_range = self.request.query_params.get('date_range', '')
        if date_range:
            try:
                if ',' in date_range:
                    start_date, end_date = date_range.split(',')
                else:
                    start_date, end_date = date_range.split(' to ')
                queryset = queryset.filter(date__range=[start_date, end_date])
            except Exception as e:
                pass

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-date', 'employee__last_name')

    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"User {self.request.user.username} created attendance record for employee {serializer.validated_data['employee'].id}")

    # @action(detail=False, methods=['get'], url_path='summary', permission_classes=[IsAdminOrHRorStaff])
    # def summary(self, request):
    #     try:
    #         year = int(request.query_params.get('year', timezone.localdate().year))
    #         month = int(request.query_params.get('month', timezone.localdate().month))
    #     except ValueError:
    #         logger.error(f"Invalid year/month parameters: {request.query_params}")
    #         return Response({'error': 'Paramètres year/month invalides'}, status=400)

    #     today = timezone.localdate()
    #     is_current_month = (year == today.year and month == today.month)
    #     present_count = 0
    #     absent_count = 0
    #     leave_count = 0
    #     if is_current_month:
    #         present_count = AttendanceRecord.objects.filter(date=today, status='present').count()
    #         absent_count = AttendanceRecord.objects.filter(date=today, status='absent').count()
    #         leave_count = AttendanceRecord.objects.filter(date=today, status='leave').count()

    #     # Fix: get correct days_in_month, never use month+1
    #     try:
    #         _, days_in_month = calendar.monthrange(year, month)
    #     except Exception as e:
    #         logger.error(f"Invalid year/month for calendar: {year}-{month}: {e}")
    #         return Response({'error': 'Paramètres year/month invalides'}, status=400)

    #     # calendar_data = []
    #     # total_employees = Employee.objects.count() or 1
    #     # for day in range(1, days_in_month + 1):
    #     #     date = datetime.date(year, month, day)
    #     #     absences = AttendanceRecord.objects.filter(date=date, status='absent').count()
    #     #     absence_rate = absences / total_employees
    #     #     calendar_data.append({'date': date.strftime('%Y-%m-%d'), 'absence_rate': absence_rate})

    #     calendar_data = []
    #     total_employees = Employee.objects.count() or 1
    #     for day in range(1, days_in_month + 1):
    #         date_val = datetime.date(year, month, day)
    #         present = AttendanceRecord.objects.filter(date=date_val, status='present').count()
    #         absent = AttendanceRecord.objects.filter(date=date_val, status='absent').count()
    #         leave = AttendanceRecord.objects.filter(date=date_val, status='leave').count() if 'leave' in [c[0] for c in AttendanceRecord._meta.get_field('status').choices] else 0
    #         calendar_data.append({
    #             'date': date_val.strftime('%Y-%m-%d'),
    #             'present': present,
    #             'absent': absent,
    #             'leave': leave,
    #             'present_rate': present / total_employees,
    #             'absent_rate': absent / total_employees,
    #             'leave_rate': leave / total_employees,
    #         })

    #     # Trend data (last 30 days from end of selected month)
    #     end_date = datetime.date(year, month, days_in_month)
    #     trend_data = []
    #     for i in range(30, -1, -1):
    #         date = end_date - datetime.timedelta(days=i)
    #         absences = AttendanceRecord.objects.filter(date=date, status='absent').count()
    #         absence_rate = absences / total_employees
    #         trend_data.append({'date': date.strftime('%Y-%m-%d'), 'absence_rate': absence_rate})

    #     logger.info(f"User {request.user.username} fetched attendance summary for {year}-{month}")
    #     return Response({
    #         'present_count': present_count,
    #         'absent_count': absent_count,
    #         'leave_count': leave_count,
    #         'calendar_data': calendar_data,
    #         'trend_data': trend_data
    #     })

    @action(detail=False, methods=['get'], url_path='summary', permission_classes=[IsAdminOrHRorStaff])
    def summary(self, request):
        try:
            year = int(request.query_params.get('year', timezone.localdate().year))
            month = int(request.query_params.get('month', timezone.localdate().month))
        except ValueError:
            logger.error(f"Invalid year/month parameters: {request.query_params}")
            return Response({'error': 'Paramètres year/month invalides'}, status=400)

        today = timezone.localdate()
        is_current_month = (year == today.year and month == today.month)

        present_count = absent_count = leave_count = 0
        if is_current_month:
            present_count = AttendanceRecord.objects.filter(date=today, status='present').count()
            absent_count = AttendanceRecord.objects.filter(date=today, status='absent').count()
            leave_count = AttendanceRecord.objects.filter(date=today, status='leave').count()

        # Month bounds
        _, days_in_month = calendar.monthrange(year, month)
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, days_in_month)

        # Calendar data (unchanged)
        total_employees = Employee.objects.count() or 1
        calendar_data = []
        for d in range(1, days_in_month + 1):
            dt = datetime.date(year, month, d)
            present = AttendanceRecord.objects.filter(date=dt, status='present').count()
            absent = AttendanceRecord.objects.filter(date=dt, status='absent').count()
            leave = AttendanceRecord.objects.filter(date=dt, status='leave').count()
            calendar_data.append({
                'date': dt.strftime('%Y-%m-%d'),
                'present': present, 'absent': absent, 'leave': leave,
                'present_rate': present/total_employees,
                'absent_rate': absent/total_employees,
                'leave_rate': leave/total_employees,
            })

        # Trend data (unchanged)
        trend_data = []
        for i in range(30, -1, -1):
            dt = end_date - datetime.timedelta(days=i)
            absences = AttendanceRecord.objects.filter(date=dt, status='absent').count()
            trend_data.append({'date': dt.strftime('%Y-%m-%d'), 'absence_rate': absences/total_employees})

        # ---------- NEW: Site & Region analytics via FKs ----------
        worksites = (Worksite.objects.filter(active=True)
                    .select_related('region')
                    .annotate(headcount=Count('employees')))

        site_meta = {
            str(ws.id): {
                'name': ws.name,
                'region_id': str(ws.region_id) if ws.region_id else None,
                'region': ws.region.name if ws.region_id else '—',
                'headcount': ws.headcount
            } for ws in worksites
        }

        # Unassigned employees bucket (no primary_worksite)
        unassigned_headcount = Employee.objects.filter(primary_worksite__isnull=True).count()
        if unassigned_headcount:
            site_meta['UNASSIGNED'] = {'name': 'Non affectés', 'region_id': None, 'region': '—', 'headcount': unassigned_headcount}

        # Today by site
        today_qs = (AttendanceRecord.objects.filter(date=today)
                    .values('employee__primary_worksite')
                    .annotate(
                        present=Count('id', filter=Q(status='present')),
                        absent=Count('id', filter=Q(status='absent')),
                        leave=Count('id', filter=Q(status='leave')),
                    ))
        today_map = {}
        for r in today_qs:
            key = str(r['employee__primary_worksite']) if r['employee__primary_worksite'] else 'UNASSIGNED'
            today_map[key] = {'present': r['present'], 'absent': r['absent'], 'leave': r['leave']}

        # Month by site
        month_qs = (AttendanceRecord.objects.filter(date__range=[start_date, end_date])
                    .values('employee__primary_worksite')
                    .annotate(
                        present=Count('id', filter=Q(status='present')),
                        absent=Count('id', filter=Q(status='absent')),
                        leave=Count('id', filter=Q(status='leave')),
                    ))
        month_map = {}
        for r in month_qs:
            key = str(r['employee__primary_worksite']) if r['employee__primary_worksite'] else 'UNASSIGNED'
            month_map[key] = {'present': r['present'], 'absent': r['absent'], 'leave': r['leave']}

        # Build site_stats
        site_ids = set(site_meta.keys()) | set(today_map.keys()) | set(month_map.keys())
        site_stats = []
        for sid in site_ids:
            meta = site_meta.get(sid, {'name': 'Site inconnu', 'region': '—', 'region_id': None, 'headcount': 0})
            td = today_map.get(sid, {'present': 0, 'absent': 0, 'leave': 0})
            md = month_map.get(sid, {'present': 0, 'absent': 0, 'leave': 0})
            today_total = td['present'] + td['absent'] + td['leave']
            month_total = md['present'] + md['absent'] + md['leave']
            site_stats.append({
                'worksite_id': sid,
                'name': meta['name'],
                'region_id': meta['region_id'],
                'region': meta['region'],
                'headcount': meta['headcount'],
                'present_today': td['present'],
                'absent_today': td['absent'],
                'leave_today': td['leave'],
                'absence_rate_today': (td['absent']/today_total) if today_total else 0.0,
                'month_present': md['present'],
                'month_absent': md['absent'],
                'month_leave': md['leave'],
                'month_total_marks': month_total,
                'month_absence_rate': (md['absent']/month_total) if month_total else 0.0,
            })

        # Region aggregates from Region model (with quotas from DB)
        region_stats_map = {}
        for s in site_stats:
            region_id = s['region_id'] or '—'
            bucket = region_stats_map.setdefault(region_id, {
                'region_id': region_id,
                'region': s['region'],
                'headcount': 0,
                'present_today': 0,
                'absent_today': 0,
                'leave_today': 0,
                'month_absent': 0,
                'month_total_marks': 0,
                'quota': 0,
            })
            bucket['headcount'] += s['headcount']
            bucket['present_today'] += s['present_today']
            bucket['absent_today'] += s['absent_today']
            bucket['leave_today'] += s['leave_today']
            bucket['month_absent'] += s['month_absent']
            bucket['month_total_marks'] += s['month_total_marks']

        # Fill quotas from DB
        for rid, bucket in list(region_stats_map.items()):
            if rid == '—' or rid is None:
                bucket['quota'] = 0
                continue
            try:
                region = Region.objects.get(id=rid)
                bucket['quota'] = region.quota or 0
                bucket['region'] = region.name  # ensure canonical name
            except Region.DoesNotExist:
                bucket['quota'] = 0

        region_stats = []
        for r in region_stats_map.values():
            today_total = r['present_today'] + r['absent_today'] + r['leave_today']
            r['absence_rate_today'] = (r['absent_today']/today_total) if today_total else 0.0
            r['month_absence_rate'] = (r['month_absent']/r['month_total_marks']) if r['month_total_marks'] else 0.0
            r['quota_gap'] = r['headcount'] - (r['quota'] or 0)
            region_stats.append(r)

        # Leaderboard
        top_absent_sites = sorted(site_stats, key=lambda s: s['absence_rate_today'], reverse=True)[:5]

        return Response({
            'present_count': present_count,
            'absent_count': absent_count,
            'leave_count': leave_count,
            'calendar_data': calendar_data,
            'trend_data': trend_data,
            'site_stats': site_stats,
            'region_stats': region_stats,
            'top_absent_sites': top_absent_sites,
        })


        @action(detail=False, methods=['get'], url_path='mine', permission_classes=[IsAuthenticated])
        def my_attendance(self, request):
            # Try Employee.user first (classic link)
            employee = Employee.objects.filter(user=request.user).first()
            if not employee:
                # Fallback to User.employee_profile (optional link)
                employee = getattr(request.user, 'employee_profile', None)

            if not employee:
                logger.warning(f"User {request.user.username} has no associated employee record")
                return Response({'error': 'Aucun employé associé à cet utilisateur'}, status=400)

            queryset = AttendanceRecord.objects.filter(employee=employee).order_by('-date')
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)


@login_required
def attendance_dashboard_view(request):
    if not (request.user.role in ['ADMIN', 'HR'] or request.user.is_staff):
        logger.warning(f"User {request.user.username} attempted unauthorized access to attendance dashboard")
        return render(request, 'attendance/attendance_dashboard.html', {'can_edit_delete': False})
    return render(request, 'attendance/attendance_dashboard.html', {'can_edit_delete': True})

@login_required
def attendance_list_view(request):
    return render(request, 'attendance/attendance_list.html', {
        'can_edit_delete': request.user.role in ['ADMIN', 'HR'] or request.user.is_staff
    })

@login_required
def attendance_create_view(request):
    if not (request.user.role in ['ADMIN', 'HR'] or request.user.is_staff):
        logger.warning(f"User {request.user.username} attempted unauthorized access to attendance create")
        return render(request, 'attendance/attendance_create.html', {'can_edit_delete': False})
    return render(request, 'attendance/attendance_create.html', {'can_edit_delete': True})

@login_required
def my_attendance_view(request):
    return render(request, 'attendance/my_attendance.html')


from django.contrib.auth.decorators import login_required, user_passes_test

def hr_or_admin(user):
    return user.is_authenticated and (user.role in ['ADMIN', 'HR'] or user.is_staff)



@require_GET
def attendance_view_detail(request, pk):
    try:
        pk = int(pk)
    except ValueError:
        return JsonResponse({'error': 'Invalid ID format'}, status=400)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if not (request.user.role in ['ADMIN', 'HR'] or request.user.is_staff):
        return JsonResponse({'error': 'Forbidden'}, status=403) 
    # Fetch the attendance record
    record = get_object_or_404(AttendanceRecord, pk=pk)
    serializer = AttendanceRecordSerializer(record)
    return JsonResponse(serializer.data, safe=False)

@csrf_exempt
@require_http_methods(["GET", "PATCH", "POST"])
@login_required
@user_passes_test(hr_or_admin)
def attendance_edit_detail(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk)
    if request.method == "GET":
        serializer = AttendanceRecordSerializer(record)
        return JsonResponse(serializer.data, safe=False)
    
    # PATCH or POST (allow both for JS compatibility)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # For PATCH, only update provided fields
    serializer = AttendanceRecordSerializer(record, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)
    return JsonResponse(serializer.errors, status=400)


# attendance/views.py
@csrf_exempt
@require_http_methods(["GET", "DELETE"])
@login_required
@user_passes_test(hr_or_admin)
def attendance_delete_detail(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk)
    if request.method == "GET":
        serializer = AttendanceRecordSerializer(record)
        return JsonResponse(serializer.data, safe=False)
    record.delete()
    return JsonResponse({'success': True})
