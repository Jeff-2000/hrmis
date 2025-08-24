from rest_framework.permissions import BasePermission

class IsExternalSystem(BasePermission):
    """
    Only allow calls from integration users (e.g., role INTEGRATION / SYSTEM / BANK / DEVICE).
    Adjust to your auth model.
    """
    ALLOWED_ROLES = {"INTEGRATION", "SYSTEM", "BANK", "DEVICE", "ADMIN"}

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        role = getattr(user, "role", None)
        return bool(user and user.is_authenticated and (role in self.ALLOWED_ROLES or user.is_staff))
