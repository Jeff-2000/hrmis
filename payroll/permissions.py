# payroll/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrHR(BasePermission):
    def has_permission(self, request, view):
        role = (getattr(request.user, 'role', '') or '').upper()
        return role in ('HR','ADMIN')

class IsSelfOrHR(BasePermission):
    def has_object_permission(self, request, view, obj):
        role = (getattr(request.user, 'role', '') or '').upper()
        if role in ('HR','ADMIN'): return True
        # payslip visibility for employee
        return getattr(obj, 'employee_id', None) == getattr(getattr(request.user, 'employee', None), 'id', None)

class HRAdminWriteSelfReadOnly(BasePermission):
    """
    HR/ADMIN: full access.
    Others: read-only and only their own contracts.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = (getattr(request.user, 'role', '') or '').upper()
        if request.method in SAFE_METHODS:
            if role in ('HR','ADMIN'):
                return True
            emp = getattr(request.user, 'employee', None)
            return emp and obj.employee_id == emp.id
        return role in ('HR','ADMIN')
