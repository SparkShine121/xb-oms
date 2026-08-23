import pytest
from decimal import Decimal

from apps.finance.models import PaymentIn
from apps.orders.models import Order
from apps.basic_info.models import Customer

@pytest.fixture
def setup(db):
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='1000.00')
    return {'order': o}

def test_payment_in_crud(setup):
    s = setup
    # create
    p = PaymentIn.objects.create(
        order=s['order'], amount_usd=Decimal('300.00'),
        payment_date='2026-08-01', installment=1, note='首期款',
    )
    assert p.pk is not None
    assert p.installment == 1
    assert p.note == '首期款'
    # read
    got = PaymentIn.objects.get(pk=p.pk)
    assert got.order_id == s['order'].id
    assert got.amount_usd == Decimal('300.00')
    # update
    got.amount_usd = Decimal('500.00')
    got.save()
    got.refresh_from_db()
    assert got.amount_usd == Decimal('500.00')
    # delete
    got.delete()
    assert PaymentIn.objects.count() == 0

def test_order_fk_related_name(setup):
    """order.payments_in 反向关联可用，删除订单级联删除回款。"""
    s = setup
    PaymentIn.objects.create(order=s['order'], amount_usd=Decimal('100.00'), payment_date='2026-08-02')
    PaymentIn.objects.create(order=s['order'], amount_usd=Decimal('200.00'), payment_date='2026-08-03', installment=2)
    assert s['order'].payments_in.count() == 2
    total = sum(p.amount_usd for p in s['order'].payments_in.all())
    assert total == Decimal('300.00')
    # 级联删除
    s['order'].delete()
    assert PaymentIn.objects.count() == 0

def test_defaults_and_str(setup):
    s = setup
    p = PaymentIn.objects.create(order=s['order'], amount_usd=Decimal('50.00'), payment_date='2026-08-04')
    assert p.installment == 1  # 默认第 1 期
    assert p.note == ''  # 备注可空
    assert str(p)  # __str__ 不报错
