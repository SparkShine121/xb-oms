from rest_framework import serializers
from .models import Order, OrderItem, ExchangeRate, calc_order_profit


class OrderItemSerializer(serializers.ModelSerializer):
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

    def validate(self, attrs):
        # 派单类字段（业务员/跟单员）仅 admin 可改：非 admin 更新时忽略，防止绕过前端直接调 API
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and self.instance is not None \
                and not user.groups.filter(name='admin').exists():
            attrs.pop('salesman', None)
            attrs.pop('tracker', None)
        return attrs

    def create(self, validated):
        items = validated.pop('items', [])
        order = Order.objects.create(**validated)
        for it in items:
            OrderItem.objects.create(order=order, **it)
        calc_order_profit(order)
        return order

    def update(self, instance, validated):
        items = validated.pop('items', None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for it in items:
                OrderItem.objects.create(order=instance, **it)
        calc_order_profit(instance)
        return instance


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ['id', 'currency_pair', 'rate', 'effective_date', 'created_at', 'updated_at']