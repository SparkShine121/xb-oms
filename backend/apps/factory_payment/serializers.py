from rest_framework import serializers
from .models import FactoryPayment, FactoryPaymentRecord

class FactoryPaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactoryPaymentRecord
        fields = ['id', 'factory_payment', 'amount', 'payment_date', 'note',
                  'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['is_approved', 'created_at', 'updated_at']

class FactoryPaymentSerializer(serializers.ModelSerializer):
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
