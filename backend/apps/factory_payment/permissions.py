from rest_framework.permissions import BasePermission

class FactoryPaymentPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups or 'finance' in groups:
            # 删除仅限 admin（设计规定）
            if view.action == 'destroy' and 'admin' not in groups:
                return False
            return True
        if view.action in ('create', 'update', 'partial_update', 'destroy', 'generate_by_order'):
            return False
        return True
