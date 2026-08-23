from rest_framework.permissions import BasePermission


class FinancePermission(BasePermission):
    """操作级权限：admin 全权；finance 可新增/修改（不可删除）；其余角色只读。"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        if 'admin' in groups:
            return True
        if view.action in ('create', 'update', 'partial_update'):
            return 'finance' in groups
        if view.action == 'destroy':
            return False  # 仅 admin（上面已放行）
        return True  # list/retrieve/ledger/export 只要登录
