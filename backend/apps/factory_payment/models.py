from decimal import Decimal

from django.db import models
from apps.orders.models import OrderItem
from apps.basic_info.models import Factory

class FactoryPayment(models.Model):
    order_item = models.OneToOneField(
        OrderItem, on_delete=models.CASCADE, related_name='factory_payment'
    )
    factory = models.ForeignKey(
        Factory, on_delete=models.CASCADE, related_name='factory_payments'
    )
    amount_cny = models.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=16, default='未结')
    note = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)  # 审批流：新建时 False，admin 通过后 True
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # 字段值可能为 str/int（未经过 to_python），统一转 Decimal 再比较
        paid = Decimal(self.paid_amount)
        amount = Decimal(self.amount_cny)
        if paid >= amount and amount > 0:
            self.status = '已结'
        elif paid > 0:
            self.status = '部分结'
        else:
            self.status = '未结'
        super().save(*args, **kwargs)

class FactoryPaymentRecord(models.Model):
    factory_payment = models.ForeignKey(
        FactoryPayment, on_delete=models.CASCADE, related_name='records'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField()
    note = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)  # 审批流：新建时 False，admin 通过后 True
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 同步父单已付金额 = 全部记录之和，并触发父单 status 重算
        fp = self.factory_payment
        total = fp.records.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        fp.paid_amount = total
        fp.save()

    def delete(self, *args, **kwargs):
        fp = self.factory_payment
        super().delete(*args, **kwargs)
        # 删除记录后回退父单已付金额（求和需在删除之后，delete 仅限 admin）
        total = fp.records.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        fp.paid_amount = total
        fp.save()
