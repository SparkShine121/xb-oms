from django.db import models

from apps.basic_info.models import LogisticsProvider
from apps.orders.models import Order


class Logistics(models.Model):
    CURRENCY_CHOICES = [('CNY', '人民币'), ('USD', '美元')]
    PAYER_CHOICES = [('customer', '客户'), ('company', '公司'), ('factory', '工厂')]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='shipments'
    )
    seq = models.IntegerField()  # 第几次发货（save 创建时自动 = 同订单已有条数 + 1）
    domestic_carrier = models.ForeignKey(
        LogisticsProvider, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='domestic_shipments'
    )
    intl_method = models.ForeignKey(
        LogisticsProvider, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='intl_shipments'
    )
    tracking_no = models.CharField(max_length=128, blank=True)
    cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost_currency = models.CharField(max_length=8, choices=CURRENCY_CHOICES, default='CNY')
    payer = models.CharField(max_length=16, choices=PAYER_CHOICES, default='company')
    note = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)  # 审批流：新建时 False，admin 通过后 True
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'seq']
        constraints = [
            # BUG-SIM-008：同订单发货序号唯一（并发重号兜底，应用层另有行锁排队）
            models.UniqueConstraint(fields=['order', 'seq'], name='logistics_order_seq_unique'),
        ]

    def __str__(self):
        return f'{self.order_id}#{self.seq}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            # BUG-SIM-008 followup：max(seq)+1 而非 count+1——删除中间序号后
            # count+1 会撞唯一约束永久阻断该订单发货登记
            from django.db.models import Max
            self.seq = (self.order.shipments.aggregate(m=Max('seq'))['m'] or 0) + 1
        super().save(*args, **kwargs)
