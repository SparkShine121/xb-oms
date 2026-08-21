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

def test_generate_by_order(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.count() == 1
    fp = FactoryPayment.objects.first()
    assert str(fp.amount_cny) == '72.00'

def test_generate_skips_existing(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.count() == 1

def test_payment_record_updates_status(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.post('/api/factory-payment/records/', {
        'factory_payment': fp.id, 'amount': '30.00', 'payment_date': '2026-08-14'
    }, format='json')
    assert r.status_code == 201
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '30.00'
    assert fp.status == '部分结'

def test_statement(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.get('/api/factory-payment/payments/statement/', {'factory': f.id})
    assert r.status_code == 200
    assert 'total_amount' in r.data['data']
