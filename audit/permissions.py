from rest_framework import permissions

class IsAdminOrAuditorOrStaff(permissions.BasePermission):
    """Allows access only to Admin, HR roles, or is_staff users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in ['ADMIN', 'AUDITOR']
                or request.user.is_staff
            )
        )
        