from rest_framework import serializers

from .models import PaymentIn


class PaymentInSerializer(serializers.ModelSerializer):
    def validate_amount_usd(self, value):
        # BUG-SIM-006：回款金额必须为正（负数回款在流水中会表现为正收入）
        if value <= 0:
            raise serializers.ValidationError('回款金额必须大于 0')
        return value

    order_no = serializers.CharField(source='order.order_no', read_only=True)

    class Meta:
        model = PaymentIn
        fields = ['id', 'order', 'order_no', 'amount_usd', 'payment_date',
                  'installment', 'note', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
