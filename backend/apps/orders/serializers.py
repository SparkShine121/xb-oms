from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Order, OrderItem, ExchangeRate, calc_order_profit
from .services import check_items_diff


class OrderItemSerializer(serializers.ModelSerializer):
    # BUG-SIM-002：可写 id 作为 diff 更新的行锚点（新建行不传）
    id = serializers.IntegerField(required=False)

    class Meta:
        model = OrderItem
        fields = ['id', 'seq', 'product', 'factory', 'model', 'product_no', 'spec',
                  'qty', 'unit_price', 'subtotal', 'cost_price', 'profit_usd',
                  'profit_rate']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    salesman_name = serializers.CharField(source='salesman.username', read_only=True, default='')
    tracker_name = serializers.CharField(source='tracker.username', read_only=True, default='')

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'ali_status', 'tracking_status', 'order_date',
                  'customer', 'salesman', 'tracker',
                  'amount_usd', 'freight', 'insurance', 'surcharge', 'service_fee_usd', 'transport_cost',
                  'carrier', 'logistics_method', 'tracking_no', 'remark', 'is_cancelled', 'order_profit_usd',
                  'is_approved', 'customer_name', 'salesman_name', 'tracker_name', 'items',
                  'created_at', 'updated_at']
        read_only_fields = ['order_profit_usd', 'is_approved']
        extra_kwargs = {
            # BUG-SIM-016：去掉自动 UniqueValidator，用带订单号的业务文案
            'order_no': {'validators': []},
        }

    def validate_order_no(self, value):
        qs = Order.objects.filter(order_no=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f'订单号 {value} 已存在')
        return value

    def validate_tracker(self, value):
        # BUG-SIM-014 Q3:a：tracker 目标必须为 tracker 角色（admin 建单/编辑同规则）。
        # 非 admin 建单时该字段会被 validate() 剔除（Q1' 忽略语义），故此处不拦截，
        # 让 payload 杂音被静默忽略而非报错。
        if value is not None and not value.groups.filter(name='tracker').exists():
            request = self.context.get('request')
            user = getattr(request, 'user', None)
            creating_non_admin = (
                self.instance is None and user is not None
                and not user.groups.filter(name='admin').exists())
            if not creating_non_admin:
                raise serializers.ValidationError('目标用户必须为跟单员（tracker）角色')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and not user.groups.filter(name='admin').exists():
            if self.instance is not None:
                # 更新：派单字段仅 admin 可改（既有规则）
                attrs.pop('salesman', None)
                attrs.pop('tracker', None)
            else:
                # BUG-SIM-004 Q1'：非 admin 建单归属=建单人，限自己客户；tracker 忽略
                customer = attrs.get('customer')
                if customer is not None and customer.salesman_id != user.id:
                    raise serializers.ValidationError('只能为自己客户的订单录入')
                attrs['salesman'] = user
                attrs.pop('tracker', None)
        return attrs

    def create(self, validated):
        items = validated.pop('items', [])
        order = Order.objects.create(**validated)
        for it in items:
            it.pop('id', None)  # 新建订单不携带明细 id
            OrderItem.objects.create(order=order, **it)
        calc_order_profit(order)
        return order

    def update(self, instance, validated):
        """BUG-SIM-002：items 改为 diff 更新——带 id 原位更新、无 id 新建、
        缺失才删除；删除已挂结算明细/修改结算行金额 → 整单 400 零写入。"""
        items = validated.pop('items', None)
        with transaction.atomic():
            for k, v in validated.items():
                setattr(instance, k, v)
            instance.save()
            if items is not None:
                check_items_diff(instance, items)  # 先校验，冲突即回滚
                existing = {it.id: it for it in instance.items.all()}
                keep_ids = set()
                for payload in items:
                    iid = payload.get('id')
                    if iid:
                        if iid not in existing:
                            raise serializers.ValidationError(f'明细 id={iid} 不属于订单 {instance.order_no}')
                        obj = existing[iid]
                        for k, v in payload.items():
                            if k != 'id':
                                setattr(obj, k, v)
                        obj.save()
                        keep_ids.add(iid)
                    else:
                        payload.pop('id', None)
                        OrderItem.objects.create(order=instance, **payload)
                for iid, obj in existing.items():
                    if iid not in keep_ids:
                        obj.delete()
            calc_order_profit(instance)
        return instance


class ExchangeRateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        # BUG-SIM-007：同币种对同日期唯一
        pair = attrs.get('currency_pair') or getattr(self.instance, 'currency_pair', None)
        date = attrs.get('effective_date') or getattr(self.instance, 'effective_date', None)
        if pair and date:
            qs = ExchangeRate.objects.filter(currency_pair=pair, effective_date=date)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(f'{pair} 在 {date} 已有汇率记录，如需调整请编辑原记录')
        return attrs

    def validate_rate(self, value):
        # BUG-SIM-012：汇率必须为正（rate=0 会把毛利整体清零）
        if value <= 0:
            raise serializers.ValidationError('汇率必须大于 0')
        return value

    class Meta:
        model = ExchangeRate
        fields = ['id', 'currency_pair', 'rate', 'effective_date', 'created_at', 'updated_at']
        # BUG-SIM-007 followup：覆写自动唯一校验器文案
        validators = [
            UniqueTogetherValidator(
                queryset=ExchangeRate.objects.all(), fields=['currency_pair', 'effective_date'],
                message='同币种对同日期的汇率记录已存在，如需调整请编辑原记录'),
        ]