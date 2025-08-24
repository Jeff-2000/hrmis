from rest_framework.permissions import BasePermission
from django.utils.timezone import now

# class CanEditDeleteOwnSituation(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.method in ['PUT', 'PATCH', 'DELETE']:
#             today = now().date()
#             return (
#                 request.user == obj.employee.user and
#                 obj.status == 'en attente' and
#                 obj.start_date > today
#             )
#         return True
    
# situation/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.utils.timezone import now

class CanEditDeleteOwnSituation(BasePermission):
    """
    - HR/ADMIN: always yes for write ops
    - Others: only if it's their own situation, status == 'en attente', and start_date > today.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        role = (getattr(request.user, 'role', '') or '').upper()
        if role in ('HR', 'ADMIN'):
            return True
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            today = now().date()
            return (
                request.user == getattr(obj.employee, 'user', None) and
                (obj.status or '').lower() == 'en attente' and
                obj.start_date > today
            )
        return False





