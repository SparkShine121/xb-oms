from django.conf import settings
from django.db import models


class ApprovalRequest(models.Model):
    """审批申请：非 admin 新建结算/付款/订单变更/物流单时挂起，admin 通过后生效。"""

    APPROVAL_TYPE_CHOICES = [
        ('settlement', '工厂结算'),
        ('payment', '工厂付款'),
        ('order_change', '订单变更'),
        ('logistics', '物流发货'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]

    approval_type = models.CharField(max_length=32, choices=APPROVAL_TYPE_CHOICES)
    target_id = models.IntegerField()
    target_model = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default='pending', choices=STATUS_CHOICES)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approval_requests')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reviewed_requests')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class OperationLog(models.Model):
    """操作日志：middleware 自动拦截写请求（POST/PUT/PATCH/DELETE）记录。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='operation_logs')
    action = models.CharField(max_length=16)
    model_name = models.CharField(max_length=64, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    path = models.CharField(max_length=256)
    detail = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class BackupRecord(models.Model):
    """备份记录：审批通过自动触发 / 手动触发，滚动保留最近 1000 份。"""

    TRIGGER_CHOICES = [
        ('approval', '审批通过自动备份'),
        ('manual', '手动备份'),
    ]

    file_path = models.CharField(max_length=256)
    file_size = models.IntegerField(default=0)
    trigger = models.CharField(max_length=16, default='manual', choices=TRIGGER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
