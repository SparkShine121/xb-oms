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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'seq']

    def __str__(self):
        return f'{self.order_id}#{self.seq}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.seq = self.order.shipments.count() + 1
        super().save(*args, **kwargs)
