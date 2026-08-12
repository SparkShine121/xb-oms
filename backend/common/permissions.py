from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    allowed_roles = []  # 子类填 group 名

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        return bool(set(self.allowed_roles) & groups)

class AdminWriteOthersReadOnly(RolePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return False
