"""审批流共享逻辑：业务 ViewSet 的 create/update 挂起与重提。"""

from .models import ApprovalRequest


def resubmit_on_update(user, instance, approval_type, target_model):
    """非 admin 更新未批准的记录时维护审批申请（驳回后可改可重提）。

    规则（标记不阻断方案）：
    - admin 编辑：不干预（admin 即审批人）
    - 目标已批准（is_approved=True）：编辑不重新挂审，直接放行
    - 该目标已有待审申请：不重复创建
    - 其余（典型为被驳回）：生成新 ApprovalRequest 重提审批
    """
    if user.groups.filter(name='admin').exists():
        return
    if getattr(instance, 'is_approved', True):
        return
    latest = (ApprovalRequest.objects
              .filter(target_model=target_model, target_id=instance.id)
              .order_by('-id').first())
    if latest and latest.status == 'pending':
        return
    ApprovalRequest.objects.create(
        approval_type=approval_type, target_id=instance.id,
        target_model=target_model, submitted_by=user)
