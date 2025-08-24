#leave/permissions.py
from rest_framework.permissions import BasePermission
from django.utils.timezone import now

class CanEditDeleteOwnLeave(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            today = now().date()
            return (request.user == obj.employee.user and
                    obj.status == 'pending' and
                    obj.start_date > today)
        return True