import pytest
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, Customer
from django.contrib.auth.models import User

@pytest.fixture
def setup(db):
    f = Factory.objects.create(name='华鑫')
    u = User.objects.create_user('admin1', password='pw123456')
    c = Customer.objects.create(name='客户A', salesman=None)
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    return {'factory': f, 'order': o, 'item': item, 'user': u}

def test_factory_payment_status_auto(setup):
    s = setup
    fp = FactoryPayment.objects.create(
        order_item=s['item'], factory=s['factory'], amount_cny='72.00'
    )
    assert fp.status == '未结'
    assert fp.paid_amount == 0

    FactoryPaymentRecord.objects.create(
        factory_payment=fp, amount='30.00', payment_date='2026-08-14'
    )
    fp.refresh_from_db()
    assert fp.paid_amount == 30
    assert fp.status == '部分结'

    FactoryPaymentRecord.objects.create(
        factory_payment=fp, amount='42.00', payment_date='2026-08-15'
    )
    fp.refresh_from_db()
    assert fp.paid_amount == 72
    assert fp.status == '已结'

def test_factory_payment_onetoone(setup):
    s = setup
    FactoryPayment.objects.create(
        order_item=s['item'], factory=s['factory'], amount_cny='72.00'
    )
    with pytest.raises(Exception):
        FactoryPayment.objects.create(
            order_item=s['item'], factory=s['factory'], amount_cny='72.00'
        )
