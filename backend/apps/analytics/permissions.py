from common.permissions import RolePermission


class AnalyticsPermission(RolePermission):
    """数据分析仪表盘属管理功能：admin/finance 可见全量，其余角色 403。"""

    allowed_roles = ['finance']
