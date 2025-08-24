# employee/permissions.py (could also reside in a common permissions module)
from rest_framework import permissions

class IsAdminOrHRorStaff(permissions.BasePermission):
    """Allows access only to Admin, HR roles, or is_staff users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in ['ADMIN', 'HR']
                or request.user.is_staff
            )
        )
        
class IsAdminOrHR(permissions.BasePermission):
    """Allows access only to Admin, HR roles, or is_staff users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in ['ADMIN', 'HR']
                or request.user.is_staff
            )
        )

class IsOwnProfile(permissions.BasePermission):
    """Allow users to access only their own employee profile (safe methods)."""
    def has_object_permission(self, request, view, obj):
        # Assume obj is an Employee instance with a one-to-one link to User
        if not request.user or not request.user.is_authenticated:
            return False
        # Admin/HR can access any profile; normal employees only their own
        if request.user.role in ['ADMIN', 'HR']:
            return True
        return hasattr(obj, 'user') and obj.user == request.user

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", "").upper() == "MANAGER"
