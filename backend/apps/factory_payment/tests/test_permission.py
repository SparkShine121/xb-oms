import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, Customer
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def finance_client(db):
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def salesman_client(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u); return c

def test_admin_can_create(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = admin_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 201

def test_finance_can_create(db, finance_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = finance_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 201

def test_salesman_cannot_create(db, salesman_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = salesman_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 403

def test_salesman_cannot_generate(db, salesman_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = salesman_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 403

def test_finance_cannot_delete(db, finance_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = finance_client.delete(f'/api/factory-payment/payments/{fp.id}/')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(pk=fp.pk).exists()

def test_record_delete_reaggregates(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    FactoryPaymentRecord.objects.create(factory_payment=fp, amount='30.00', payment_date='2026-08-14')
    rec2 = FactoryPaymentRecord.objects.create(factory_payment=fp, amount='42.00', payment_date='2026-08-15')
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '72.00'
    assert fp.status == '已结'
    r = admin_client.delete(f'/api/factory-payment/records/{rec2.id}/')
    assert r.status_code == 200
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '30.00'
    assert fp.status == '部分结'

# ---- BUG-SIM-001: bulk-delete 权限必须等价于单条删除 ----

def _make_payment():
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    return FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')

def test_finance_cannot_bulk_delete_payments(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(id=p.id).exists()

def test_salesman_cannot_bulk_delete_payments(db, salesman_client):
    p = _make_payment()
    r = salesman_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(id=p.id).exists()

def test_admin_can_bulk_delete_payments(db, admin_client):
    p = _make_payment()
    r = admin_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 200 and r.data['data']['deleted'] == 1
    assert not FactoryPayment.objects.filter(id=p.id).exists()

# ---- BUG-SIM-006/012: 金额校验 ----

def test_negative_payment_record_rejected(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '-100', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 400
    p.refresh_from_db()
    assert str(p.paid_amount) == '0.00' and p.status == '未结'

def test_zero_payment_record_rejected(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '0', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 400

def test_overpay_record_rejected(db, finance_client):
    p = _make_payment()  # amount_cny=72
    r1 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '50', 'payment_date': '2026-09-17'}, format='json')
    assert r1.status_code == 201
    r2 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '30', 'payment_date': '2026-09-17'}, format='json')
    assert r2.status_code == 400  # 50+30 > 72
    p.refresh_from_db()
    assert str(p.paid_amount) == '50.00' and p.status == '部分结'

def test_pay_exact_amount_settles(db, finance_client):
    """回归锁：恰好付满正常放行并置已结"""
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '72', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 201
    p.refresh_from_db()
    assert p.status == '已结'

def test_overpay_via_record_update_rejected(db, finance_client):
    p = _make_payment()
    r1 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '50', 'payment_date': '2026-09-17'}, format='json')
    rid = r1.data['data']['id']
    r2 = finance_client.patch(f'/api/factory-payment/records/{rid}/', {'amount': '80'}, format='json')
    assert r2.status_code == 400  # 改大后 80 > 72
    p.refresh_from_db()
    assert str(p.paid_amount) == '50.00'

def test_non_positive_settlement_amount_rejected(db, admin_client):
    from apps.basic_info.models import Factory as FPFactory
    f = FPFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='OZ', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    for bad in ('0', '-5'):
        r = admin_client.post('/api/factory-payment/payments/',
                              {'order_item': item.id, 'factory': f.id, 'amount_cny': bad}, format='json')
        assert r.status_code == 400, bad
