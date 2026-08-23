from rest_framework import serializers

from .models import PaymentIn


class PaymentInSerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source='order.order_no', read_only=True)

    class Meta:
        model = PaymentIn
        fields = ['id', 'order', 'order_no', 'amount_usd', 'payment_date',
                  'installment', 'note', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
