from rest_framework.permissions import BasePermission


class LogisticsPermission(BasePermission):
    """操作级权限：admin 全权；tracker 可新增/修改；所有人只读；禁止删除（admin 除外）。"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        if view.action in ('create', 'update', 'partial_update'):
            return 'tracker' in groups
        if view.action == 'destroy':
            return False
        return True  # list/retrieve 只要 IsAuthenticated
