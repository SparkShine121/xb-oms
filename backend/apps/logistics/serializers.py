from rest_framework import serializers

from .models import Logistics


class LogisticsSerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source='order.order_no', read_only=True)
    carrier_name = serializers.CharField(source='domestic_carrier.name', read_only=True, default='')
    intl_name = serializers.CharField(source='intl_method.name', read_only=True, default='')

    class Meta:
        model = Logistics
        fields = ['id', 'order', 'order_no', 'seq',
                  'domestic_carrier', 'intl_method', 'carrier_name', 'intl_name',
                  'tracking_no', 'cost', 'cost_currency', 'payer', 'note',
                  'created_at', 'updated_at']
        read_only_fields = ['seq', 'created_at', 'updated_at']
