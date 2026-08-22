import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
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

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def tracker_client(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    u.groups.add(Group.objects.get(name='tracker'))
    c = APIClient(); c.force_authenticate(u); return c, u

@pytest.fixture
def salesman_client(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u); return c

def test_admin_crud(db, setup, admin_client):
    r = admin_client.get('/api/logistics/shipments/')
    assert r.status_code == 200 and len(r.data['data']['results']) >= 1
    r2 = admin_client.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'NEW'}, format='json')
    assert r2.status_code == 201
    r3 = admin_client.delete(f'/api/logistics/shipments/{setup["logistics"].id}/')
    assert r3.status_code == 200

def test_tracker_can_write_own(db, setup, tracker_client):
    tc, tr = tracker_client
    from django.contrib.auth.models import User
    setup['order'].tracker = tr; setup['order'].save()
    r = tc.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'TRK'}, format='json')
    assert r.status_code == 201

def test_salesman_readonly_scoped(db, setup, salesman_client):
    sc = salesman_client
    r = sc.get('/api/logistics/shipments/')
    assert r.status_code == 200  # 能看
    r2 = sc.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'X'}, format='json')
    assert r2.status_code == 403  # 不能写

def test_finance_readonly(db, setup):
    from django.contrib.auth.models import User, Group
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    r2 = c.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'X'}, format='json')
    assert r2.status_code == 403
