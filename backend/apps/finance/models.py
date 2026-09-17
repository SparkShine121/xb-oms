from django.core.validators import MinValueValidator
from django.db import models

from apps.orders.models import Order


class PaymentIn(models.Model):
    """回款登记：订单的每期到账记录（轻财务模块）。"""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments_in'
    )
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField()
    installment = models.IntegerField(default=1, validators=[MinValueValidator(1)])  # 第几期（BUG-SIM-007 followup：0/负数无意义）
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-id']
        constraints = [
            # BUG-SIM-006：回款金额必须为正（负数回款在流水中表现为正收入）
            models.CheckConstraint(condition=models.Q(amount_usd__gt=0), name='paymentin_amount_positive'),
            # BUG-SIM-007：同一订单同一期唯一（一期一笔到账）
            models.UniqueConstraint(fields=['order', 'installment'], name='paymentin_order_installment_unique'),
        ]

    def __str__(self):
        return f'{self.order_id}#{self.installment} {self.amount_usd}'
