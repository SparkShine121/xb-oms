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
        constraints = [
            # BUG-SIM-012：汇率必须为正（rate=0 会把毛利整体清零）
            models.CheckConstraint(condition=models.Q(rate__gt=0), name='exchangerate_rate_positive'),
            # BUG-SIM-007：同币种对同日期唯一（毛利取值确定性）
            models.UniqueConstraint(fields=['currency_pair', 'effective_date'], name='exchangerate_pair_date_unique'),
        ]

    @classmethod
    def get_effective_rate(cls, date):
        # BUG-SIM-011 followup：限定 USD/CNY（成本 CNY/售价 USD 的唯一用途币对），
        # 防止录入其他币对后被毛利折算误取
        qs = cls.objects.filter(currency_pair='USD/CNY', effective_date__lte=date).order_by('-effective_date', '-id')
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
    is_approved = models.BooleanField(default=True)  # 审批流：新建时 False，admin 通过后 True
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


def _rate_for_order(order_date):
    """取订单适用汇率（BUG-SIM-011）：日期无适用 → 回退全库最近一条；无任何汇率 → None。"""
    rate_obj = ExchangeRate.get_effective_rate(order_date) if order_date else None
    if rate_obj is None:
        rate_obj = ExchangeRate.objects.filter(currency_pair='USD/CNY').order_by('-effective_date', '-id').first()
    return rate_obj


def _apply_item_profits(items, rate):
    """按汇率就地计算各明细毛利，返回合计（供单订单/批量两条路径共用，防口径漂移）。"""
    total = Decimal('0')
    for item in items:
        if rate > 0 and item.subtotal:
            item.profit_usd = item.subtotal - (item.cost_price * item.qty / rate)
            item.profit_rate = item.profit_usd / item.subtotal if item.subtotal else Decimal('0')
        else:
            item.profit_usd = Decimal('0'); item.profit_rate = Decimal('0')
        total += item.profit_usd
    return total


def calc_order_profit(order):
    """单订单重算（建单/编辑/导入等单条路径调用）。"""
    order.refresh_from_db()
    rate_obj = _rate_for_order(order.order_date)
    rate = Decimal(str(rate_obj.rate)) if rate_obj else Decimal('1')
    total = _apply_item_profits(order.items.all(), rate)
    order.order_profit_usd = total - order.freight - order.insurance - order.surcharge - order.service_fee_usd
    order.save()


def recalc_all_orders():
    """全量批量重算（BUG-SIM-022 Q2:a：汇率增删改触发）。

    bulk_update 批量化——全库约 5 条查询（汇率 1 + 明细预取 2 + 明细/订单 bulk 各 1），
    生产 MySQL 下避免逐单 round-trip 超时。调用方需自行包 transaction.atomic。
    """
    import bisect
    orders = list(Order.objects.prefetch_related('items'))
    rates = list(ExchangeRate.objects.filter(currency_pair='USD/CNY').order_by('effective_date', 'id'))
    rate_dates = [r.effective_date for r in rates]

    def rate_for(d):
        # 与 _rate_for_order 同语义：生效日期 <= 订单日期的最新一条；无 → 全库最新一条
        if d is not None:
            i = bisect.bisect_right(rate_dates, d)
            if i > 0:
                return rates[i - 1]
        return rates[-1] if rates else None

    items_to_update, orders_to_update = [], []
    for o in orders:
        rate_obj = rate_for(o.order_date)
        rate = Decimal(str(rate_obj.rate)) if rate_obj else Decimal('1')
        total = _apply_item_profits(o.items.all(), rate)
        o.order_profit_usd = total - o.freight - o.insurance - o.surcharge - o.service_fee_usd
        items_to_update.extend(o.items.all())
        orders_to_update.append(o)
    if items_to_update:
        OrderItem.objects.bulk_update(items_to_update, ['profit_usd', 'profit_rate'])
    if orders_to_update:
        Order.objects.bulk_update(orders_to_update, ['order_profit_usd'])