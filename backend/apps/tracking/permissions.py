from rest_framework.permissions import BasePermission

class TrackingPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        if view.action in ('advance', 'reject'):
            return 'tracker' in groups
        return True  # timeline/my 只要 IsAuthenticated

    def has_object_permission(self, request, view, obj):
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups or 'finance' in groups:
            return True
        if view.action in ('advance', 'reject'):
            if 'tracker' in groups and obj.tracker_id == request.user.id:
                return True
            return False
        # timeline: salesman 自己客户、tracker 派给自己
        if 'salesman' in groups and obj.customer and obj.customer.salesman_id == request.user.id:
            return True
        if 'tracker' in groups and obj.tracker_id == request.user.id:
            return True
        return False
