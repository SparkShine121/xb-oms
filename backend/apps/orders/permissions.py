from rest_framework.permissions import BasePermission

class OrderPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        groups = set(request.user.groups.values_list('name', flat=True))
        # BUG-SIM-004 Q1'：导入是批量跨客户动作，收紧为仅 admin（归属自动按客户分配）
        if view.action == 'import_data':
            return 'admin' in groups
        if 'admin' in groups:
            return True
        if 'finance' in groups:
            # BUG-SIM-014 Q2:a：派单仅 admin，finance 只读结算域
            return view.action != 'set_tracker'
        if view.action in ('destroy', 'set_tracker'):
            return False
        if view.action == 'create':
            return 'salesman' in groups
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