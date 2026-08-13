from rest_framework.permissions import BasePermission

class OrderPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups or 'finance' in groups:
            return True
        if view.action in ('import_data', 'create'):
            return 'salesman' in groups
        if view.action in ('destroy', 'set_tracker'):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        if view.action == 'destroy':
            return False
        if view.action in ('update', 'partial_update'):
            if 'salesman' in groups and obj.customer and obj.customer.salesman_id == request.user.id:
                return True
            if 'tracker' in groups and obj.tracker_id == request.user.id:
                return True
            return False
        return True