from django.db import models
from django.contrib.auth.models import User
from apps.basic_info.models import Customer, Product, Factory
from decimal import Decimal


class ExchangeRate(models.Model):
    currency_pair = models.CharField(max_length=16, default='USD/CNY')
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date', '-id']

    @classmethod
    def get_effective_rate(cls, date):
        qs = cls.objects.filter(effective_date__lte=date).order_by('-effective_date', '-id')
        return qs.first() if qs.exists() else None


class Order(models.Model):
    TRACKING_STATUS_CHOICES = [
        ('接单','接单'),('排产','排产'),('生产中','生产中'),('质检','质检'),
        ('发货','发货'),('签收','签收'),('结算','结算'),('回款','回款'),('已取消','已取消'),
    ]
    order_no = models.CharField(max_length=64, unique=True)
    ali_status = models.CharField(max_length=32, blank=True)
    tracking_status = models.CharField(max_length=16, choices=TRACKING_STATUS_CHOICES, blank=True)
    order_date = models.DateField(null=True, blank=True)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    salesman = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='sales_orders')
    tracker = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tracked_orders')
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    freight = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    surcharge = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    service_fee_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    transport_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    carrier = models.CharField(max_length=64, blank=True)
    logistics_method = models.CharField(max_length=64, blank=True)
    tracking_no = models.CharField(max_length=128, blank=True)
    remark = models.TextField(blank=True)
    is_cancelled = models.BooleanField(default=False)
    order_profit_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    seq = models.IntegerField(default=0)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    factory = models.ForeignKey(Factory, null=True, blank=True, on_delete=models.SET_NULL)
    model = models.CharField(max_length=64, blank=True)
    product_no = models.CharField(max_length=64, blank=True)
    spec = models.TextField(blank=True)
    qty = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    profit_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    profit_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def calc_order_profit(order):
    order.refresh_from_db()
    rate_obj = ExchangeRate.get_effective_rate(order.order_date) if order.order_date else ExchangeRate.objects.order_by('-effective_date','-id').first()
    rate = Decimal(str(rate_obj.rate)) if rate_obj else Decimal('1')
    total = Decimal('0')
    for item in order.items.all():
        if rate > 0 and item.subtotal:
            item.profit_usd = item.subtotal - (item.cost_price * item.qty / rate)
            item.profit_rate = item.profit_usd / item.subtotal if item.subtotal else Decimal('0')
        else:
            item.profit_usd = Decimal('0'); item.profit_rate = Decimal('0')
        item.save()
        total += item.profit_usd
    order.order_profit_usd = total - order.freight - order.insurance - order.surcharge - order.service_fee_usd
    order.save()