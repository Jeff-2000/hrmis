# attendance/permissions.py
import math
from rest_framework.permissions import BasePermission, SAFE_METHODS
from employee.models import Employee, Worksite

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def extract_lat_lng(request):
    # Accept from JSON body, query params, or headers
    lat = request.data.get('lat') or request.query_params.get('lat') or request.headers.get('X-Geo-Lat')
    lng = request.data.get('lng') or request.query_params.get('lng') or request.headers.get('X-Geo-Lng')
    try:
        return (float(lat), float(lng))
    except (TypeError, ValueError):
        return (None, None)

class IsAdminHrManagerAndOnSite(BasePermission):
    message = "Vous devez être autorisé et présent sur le site de travail pour enregistrer la présence."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated):
            return False
        role_ok = user.is_staff or user.role in ('ADMIN', 'HR', 'MANAGER')
        if not role_ok:
            return False

        lat, lng = extract_lat_lng(request)
        if lat is None or lng is None:
            self.message = "Coordonnées géographiques manquantes (lat/lng)."
            return False

        # Figure out the target employee
        target_emp_id = request.data.get('employee') or request.data.get('employee_id')
        if not target_emp_id and hasattr(view, 'get_object') and view.action in ('update', 'partial_update'):
            # For update without body 'employee', look up instance
            instance = view.get_object()
            target_emp_id = str(instance.employee_id)

        try:
            target_emp = Employee.objects.select_related('primary_worksite', 'manager').get(id=target_emp_id)
        except Employee.DoesNotExist:
            self.message = "Employé cible introuvable."
            return False

        ws = target_emp.primary_worksite
        if not ws or ws.latitude is None or ws.longitude is None:
            self.message = "Le site de travail de l’employé n’est pas configuré."
            return False

        dist = haversine_m(lat, lng, float(ws.latitude), float(ws.longitude))
        if dist > (ws.allowed_radius_m or 150):
            self.message = "Vous êtes hors du périmètre autorisé du site."
            return False

        # If manager, ensure hierarchy
        if user.role == 'MANAGER':
            actor_emp = getattr(user, 'employee_profile', None) or getattr(user, 'employee', None)
            if not actor_emp or target_emp.manager_id != actor_emp.id:
                self.message = "Manager non autorisé pour cet employé."
                return False

        return True

    def has_object_permission(self, request, view, obj):
        # Reuse has_permission logic for object-level ops
        return self.has_permission(request, view)
