from django.db import models

from apps.orders.models import Order


class PaymentIn(models.Model):
    """回款登记：订单的每期到账记录（轻财务模块）。"""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments_in'
    )
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField()
    installment = models.IntegerField(default=1)  # 第几期
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-id']

    def __str__(self):
        return f'{self.order_id}#{self.installment} {self.amount_usd}'
