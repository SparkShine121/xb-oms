"""跟单流转服务：advance/reject 的并发安全实现（BUG-SIM-009）。

语义（grilling Q3:a 变更拒绝）：
- 事务内 select_for_update 锁订单行（生产 MySQL 真互斥；SQLite 单写者缓解）
- 锁定后比对 updated_at 指纹——请求读取后被他人动过 → ValidationError 变更拒绝，
  防双击/双操作者静默多推一格，操作者刷新后重试
- 校验基于锁定后的最新值（终态/取消判断不旁路）
"""
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.orders.models import Order
from .models import TrackingLog, TrackingPhoto
from .state_machine import next_node, prev_node


def _move(order, user, note, photos, *, is_reject):
    """order 为请求开始时读到的对象（updated_at 即指纹）；photos 为已校验的文件列表。"""
    with transaction.atomic():
        fresh = Order.objects.select_for_update().get(pk=order.pk)
        if fresh.updated_at != order.updated_at:
            raise ValidationError('订单状态已被他人更新，请刷新后操作')
        if fresh.is_cancelled:
            raise ValidationError('已取消订单不可流转')
        node = prev_node(fresh.tracking_status) if is_reject else next_node(fresh.tracking_status)
        if not node:
            raise ValidationError('当前节点不可驳回（起点）' if is_reject else '当前节点不可推进（终态）')
        log = TrackingLog.objects.create(
            order=fresh, node=node, note=note, operator=user, is_reject=is_reject)
        for p in (photos or []):
            TrackingPhoto.objects.create(tracking_log=log, image=p)
        fresh.tracking_status = node
        # updated_at 须显式列入 update_fields 才会刷新（auto_now 特性），它是并发指纹
        fresh.save(update_fields=['tracking_status', 'updated_at'])
    return log, node


def advance_order(order, user, note='', photos=None):
    return _move(order, user, note, photos, is_reject=False)


def reject_order(order, user, note='', photos=None):
    return _move(order, user, note, photos, is_reject=True)
