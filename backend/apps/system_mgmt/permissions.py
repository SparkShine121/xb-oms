from common.permissions import RolePermission


class AdminOnlyPermission(RolePermission):
    """仅 admin 可访问（审批处理/操作日志查询/备份管理均为管理员功能）。"""

    allowed_roles = []
