from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'superuser' or request.user.can_manage_users)

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check for specific permission based on the view's purpose
        # This is a bit generic, so we might need more granular permissions classes
        # or the view should use specific classes.
        # For now, let's keep it backward compatible but also check flags.
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['superuser', 'manager'] or request.user.can_manage_flocks

class CanManageFlocks(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_flocks

class CanManageFinances(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_finances

class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated # Authenticated users are at least staff
