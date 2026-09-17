from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import PaymentIn


class PaymentInSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        # BUG-SIM-007：同一订单同一期回款唯一
        order = attrs.get('order') or getattr(self.instance, 'order', None)
        installment = attrs.get('installment', getattr(self.instance, 'installment', None))
        if order is not None and installment is not None:
            qs = PaymentIn.objects.filter(order=order, installment=installment)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('该订单此期回款已登记，请修改期数或编辑原记录')
        return attrs

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
        # BUG-SIM-007 followup：覆写自动唯一校验器文案，业务友好提示可达用户
        validators = [
            UniqueTogetherValidator(
                queryset=PaymentIn.objects.all(), fields=['order', 'installment'],
                message='该订单此期回款已登记，请修改期数或编辑原记录'),
        ]
