from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Employee, Department, Grade
from .serializers import *
from django.db.models import Q, Count
from .permissions import *
import logging
import json
from django.views.decorators.http import require_GET, require_http_methods

logger = logging.getLogger(__name__)

def check_edit_delete_permission(user):
    """Check if user has HR, ADMIN, or is_staff role."""
    return user.is_authenticated and (user.role in ['ADMIN', 'HR'] or user.is_staff)

@login_required
def employee_list_view(request):
    """Render the employee list page with paginated data."""
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '')

    # Fetch employees
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    if search:
        employees = employees.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )
    if not check_edit_delete_permission(request.user):
        employees = employees.filter(user=request.user)

    # Paginate
    paginator = Paginator(employees, page_size)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
        page = 1

    # Serialize for AJAX if requested
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        serializer = EmployeeSerializer(page_obj.object_list, many=True)
        return JsonResponse({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'results': serializer.data,
            'page': int(page),
        })

    context = {
        'employees': page_obj.object_list,
        'page_obj': page_obj,
        'page_size': page_size,
        'search': search,
        'can_edit_delete': check_edit_delete_permission(request.user),
    }
    logger.debug(f"User {request.user.username} accessed employee_list, page {page}")
    return render(request, 'employee/employee_list.html', context)

@require_POST
@login_required
def employee_delete_view(request, id):
    """Handle employee deletion via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized delete of employee {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    employee = get_object_or_404(Employee, id=id)
    try:
        employee.delete()
        logger.info(f"User {request.user.username} deleted employee {id}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error deleting employee {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def employee_edit_view(request, id):
    """Handle employee editing via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized edit of employee {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    employee = get_object_or_404(Employee, id=id)
    try:
        data = json.loads(request.body)
        serializer = EmployeeSerializer(employee, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated employee {id}")
            return JsonResponse({'success': True, 'employee': serializer.data})
        return JsonResponse({'error': serializer.errors}, status=400)
    except Exception as e:
        logger.error(f"Error updating employee {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    

@require_GET
@login_required
def employee_detail_view(request, id):
    """
    Returns a single employee's data as JSON for edit/view modal.
    """
    # Optional: Restrict view for non-admins to only their own record
    if not check_edit_delete_permission(request.user):
        employee = get_object_or_404(Employee, id=id, user=request.user)
    else:
        employee = get_object_or_404(Employee, id=id)

    serializer = EmployeeSerializer(employee)
    return JsonResponse(serializer.data, safe=False)


@login_required
def employee_create_view(request):
    """Render the employee creation form and handle submissions."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized access to employee create")
        return redirect('employee_list')

    if request.method == 'POST':
        try:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Handle AJAX request
                data = json.loads(request.body)
            else:
                # Handle regular form submission
                data = request.POST.dict()
            
            serializer = EmployeeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} created new employee")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'employee': serializer.data})
                else:
                    return redirect('employee_list')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': serializer.errors}, status=400)
            else:
                # For non-AJAX, you might want to render the form with errors
                return render(request, 'employee/employee_create.html', {'errors': serializer.errors})
                
        except Exception as e:
            logger.error(f"Error creating employee: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=500)
            else:
                # Handle error for non-AJAX
                return render(request, 'employee/employee_create.html', {'error': str(e)})

    return render(request, 'employee/employee_create.html', {})

@login_required
def grade_create_view(request):
    """Render the grade creation form."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized access to grade create")
        return redirect('grade_list')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            serializer = GradeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} created new grade")
                return JsonResponse({'success': True, 'grade': serializer.data})
            return JsonResponse({'error': serializer.errors}, status=400)
        except Exception as e:
            logger.error(f"Error creating grade: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'employee/grade_create.html', {})

@login_required
def department_create_view(request):
    """Render the department creation form."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized access to department create")
        return redirect('department_list')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            serializer = DepartmentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} created new department")
                return JsonResponse({'success': True, 'department': serializer.data})
            return JsonResponse({'error': serializer.errors}, status=400)
        except Exception as e:
            logger.error(f"Error creating department: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'employee/department_create.html', {})

@require_GET
@login_required
def grade_list_api(request):
    """Return paginated list of grades with stats for dropdown or list view."""
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '')

    grades = Grade.objects.all().order_by('code')
    if search:
        grades = grades.filter(
            Q(code__icontains=search) | Q(description__icontains=search)
        )

    grades = grades.annotate(employee_count=Count('employee'))
    total_employees = sum(grade.employee_count for grade in grades)

    paginator = Paginator(grades, page_size)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
        page = 1

    serializer = GradeSerializer(page_obj.object_list, many=True)
    return JsonResponse({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'results': serializer.data,
        'page': int(page),
        'total_employees': total_employees
    })
    
    
@require_GET
@login_required
def department_list_api(request):
    """Return list of departments for dropdown population."""
    departments = Department.objects.all()
    serializer = DepartmentSerializer(departments, many=True)
    return JsonResponse({'results': serializer.data}, safe=False)




@require_GET
@login_required
def grade_detail_view(request, id):
    grade = Grade.objects.filter(id=id).annotate(employee_count=Count('employee')).first()
    if not grade:
        return JsonResponse({'error': 'Not found'}, status=404)
    serializer = GradeSerializer(grade)
    return JsonResponse(serializer.data, safe=False)


@require_http_methods(['PATCH'])
@login_required
def grade_edit_view(request, id):
    """Handle grade editing via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized edit of grade {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    grade = get_object_or_404(Grade, id=id)
    try:
        data = json.loads(request.body)
        serializer = GradeSerializer(grade, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated grade {id}")
            return JsonResponse({'success': True, 'grade': serializer.data})
        return JsonResponse({'error': serializer.errors}, status=400)
    except Exception as e:
        logger.error(f"Error updating grade {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(['DELETE'])
@login_required
def grade_delete_view(request, id):
    """Handle grade deletion via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized delete of grade {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    grade = get_object_or_404(Grade, id=id)
    try:
        if Employee.objects.filter(grade=grade).exists():
            return JsonResponse({'error': 'Impossible de supprimer ce grade : il est associé à des employés'}, status=400)
        grade.delete()
        logger.info(f"User {request.user.username} deleted grade {id}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error deleting grade {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def grade_list_view(request):
    """Render the grade list page."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return grade_list_api(request)
    return render(request, 'employee/grade_list.html', {'can_edit_delete': check_edit_delete_permission(request.user)})


@require_GET
@login_required
def department_list_api(request):
    """Return paginated list of departments with stats for dropdown or list view."""
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '')

    departments = Department.objects.all().order_by('name')
    if search:
        departments = departments.filter(
            Q(name__icontains=search) | Q(parent__name__icontains=search)
        )


    departments = departments.annotate(employee_count=Count('employees'))
    total_employees = sum(department.employee_count for department in departments)

    paginator = Paginator(departments, page_size)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
        page = 1

    serializer = DepartmentSerializer(page_obj.object_list, many=True)
    return JsonResponse({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'results': serializer.data,
        'page': int(page),
        'total_employees': total_employees
    })

@require_GET
@login_required
def department_detail_view(request, id):
    """Return a single department's data as JSON for view/edit modal."""
    department = get_object_or_404(Department, id=id)
    serializer = DepartmentSerializer(department)
    return JsonResponse(serializer.data, safe=False)

@require_http_methods(['PATCH'])
@login_required
def department_edit_view(request, id):
    """Handle department editing via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized edit of department {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    department = get_object_or_404(Department, id=id)
    try:
        data = json.loads(request.body)
        serializer = DepartmentSerializer(department, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated department {id}")
            return JsonResponse({'success': True, 'department': serializer.data})
        return JsonResponse({'error': serializer.errors}, status=400)
    except Exception as e:
        logger.error(f"Error updating department {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(['DELETE'])
@login_required
def department_delete_view(request, id):
    """Handle department deletion via AJAX."""
    if not check_edit_delete_permission(request.user):
        logger.warning(f"User {request.user.username} attempted unauthorized delete of department {id}")
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    department = get_object_or_404(Department, id=id)
    try:
        if Employee.objects.filter(department=department).exists():
            return JsonResponse({'error': 'Impossible de supprimer ce département : il est associé à des employés'}, status=400)
        department.delete()
        logger.info(f"User {request.user.username} deleted department {id}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error deleting department {id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def department_list_view(request):
    """Render the department list page."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return department_list_api(request)
    return render(request, 'employee/department_list.html', {'can_edit_delete': check_edit_delete_permission(request.user)})


@require_GET
@login_required
def department_choices_api(request):
    """Return a list of departments for parent selection."""
    departments = Department.objects.all().order_by('name')
    data = [{'id': d.id, 'name': d.name} for d in departments]
    return JsonResponse(data, safe=False)



# employee/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Employee
from .serializers import EmployeeSerializer
from rest_framework.permissions import IsAuthenticated

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], name='Get Current Employee')
    def me(self, request):
        if not request.user.employee:
            return Response({'error': 'No employee profile linked to user'}, status=400)
        serializer = self.get_serializer(request.user.employee)
        return Response(serializer.data)
