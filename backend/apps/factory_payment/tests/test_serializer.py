import pytest
from apps.factory_payment.serializers import FactoryPaymentSerializer, FactoryPaymentRecordSerializer
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, Customer

@pytest.fixture
def setup(db):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    return {'fp': fp, 'item': item, 'factory': f}

def test_serializer_fields(setup):
    s = FactoryPaymentSerializer(setup['fp'])
    assert s.data['amount_cny'] == '72.00'
    assert s.data['paid_amount'] == '0.00'
    assert s.data['status'] == '未结'
    assert s.data['factory_name'] == '华鑫'
    assert s.data['order_no'] == 'O1'
    assert isinstance(s.data['records'], list) and len(s.data['records']) == 0

def test_record_serializer(setup):
    rec = FactoryPaymentRecord.objects.create(
        factory_payment=setup['fp'], amount='30.00', payment_date='2026-08-14'
    )
    s = FactoryPaymentRecordSerializer(rec)
    assert s.data['amount'] == '30.00'
