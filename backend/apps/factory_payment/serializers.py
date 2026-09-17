from rest_framework import serializers
from .models import FactoryPayment, FactoryPaymentRecord

class FactoryPaymentRecordSerializer(serializers.ModelSerializer):
    def validate_amount(self, value):
        # BUG-SIM-006：付款金额必须为正（负数会拉低已付、0 无业务意义）
        if value <= 0:
            raise serializers.ValidationError('付款金额必须大于 0')
        return value

    class Meta:
        model = FactoryPaymentRecord
        fields = ['id', 'factory_payment', 'amount', 'payment_date', 'note',
                  'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['is_approved', 'created_at', 'updated_at']

class FactoryPaymentSerializer(serializers.ModelSerializer):
    def validate_amount_cny(self, value):
        # BUG-SIM-006 Q2:i：结算金额必须为正（0/负金额结算单是脏数据）
        if value <= 0:
            raise serializers.ValidationError('结算金额必须大于 0')
        return value

    records = FactoryPaymentRecordSerializer(many=True, read_only=True)
    factory_name = serializers.CharField(source='factory.name', read_only=True)
    order_no = serializers.CharField(source='order_item.order.order_no', read_only=True)
    product_no = serializers.CharField(source='order_item.product_no', read_only=True, default='')

    class Meta:
        model = FactoryPayment
        fields = ['id', 'order_item', 'factory', 'factory_name', 'order_no', 'product_no',
                  'amount_cny', 'paid_amount', 'status', 'note', 'records', 'is_approved',
                  'created_at', 'updated_at']
        read_only_fields = ['paid_amount', 'status', 'is_approved', 'created_at', 'updated_at']
