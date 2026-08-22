import pytest
from apps.logistics.serializers import LogisticsSerializer
from apps.logistics.models import Logistics
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, LogisticsProvider, Customer

@pytest.fixture
def setup(db):
    carrier = LogisticsProvider.objects.create(name='圆通', type='domestic')
    intl = LogisticsProvider.objects.create(name='DHL', type='international')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    logi = Logistics.objects.create(order=o, domestic_carrier=carrier, intl_method=intl, tracking_no='YT123', cost='50.00')
    return {'logistics': logi, 'order': o, 'carrier': carrier, 'intl': intl}

def test_serializer_fields(setup):
    s = LogisticsSerializer(setup['logistics'])
    assert s.data['tracking_no'] == 'YT123'
    assert s.data['cost'] == '50.00'
    assert s.data['cost_currency'] == 'CNY'
    assert s.data['payer'] == 'company'
    assert s.data['seq'] == 1
    assert s.data['order_no'] == 'O1'
    assert s.data['carrier_name'] == '圆通'
    assert s.data['intl_name'] == 'DHL'

def test_create_via_serializer(setup):
    data = {'order': setup['order'].id, 'tracking_no': 'NEW001', 'cost': '30.00'}
    s = LogisticsSerializer(data=data)
    assert s.is_valid(), s.errors
    obj = s.save()
    assert obj.tracking_no == 'NEW001'
    assert obj.seq == 2  # setup 里已有一条
