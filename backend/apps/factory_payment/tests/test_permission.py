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
