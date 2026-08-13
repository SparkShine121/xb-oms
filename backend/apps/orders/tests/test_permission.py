import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order
from apps.basic_info.models import Customer

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c, u

@pytest.fixture
def sales_client(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u); return c, u

@pytest.fixture
def tracker_client(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    u.groups.add(Group.objects.get(name='tracker'))
    c = APIClient(); c.force_authenticate(u); return c, u

def test_admin_sees_all(db, admin_client):
    c, _ = admin_client
    Order.objects.create(order_no='O1'); Order.objects.create(order_no='O2')
    r = c.get('/api/orders/orders/')
    assert r.status_code == 200
    assert len(r.data['data']['results']) == 2

def test_salesman_sees_own_customers(db, sales_client):
    c, sales = sales_client
    cust = Customer.objects.create(name='C1', salesman=sales)
    other = Customer.objects.create(name='C2')
    Order.objects.create(order_no='O1', customer=cust)
    Order.objects.create(order_no='O2', customer=other)
    r = c.get('/api/orders/orders/')
    assert len(r.data['data']['results']) == 1
    assert r.data['data']['results'][0]['order_no'] == 'O1'

def test_tracker_sees_assigned(db, tracker_client):
    c, tr = tracker_client
    Order.objects.create(order_no='O1', tracker=tr)
    Order.objects.create(order_no='O2')
    r = c.get('/api/orders/orders/')
    assert len(r.data['data']['results']) == 1
    assert r.data['data']['results'][0]['order_no'] == 'O1'

def test_only_admin_can_delete(db, sales_client, admin_client):
    sc, _ = sales_client
    ac, _ = admin_client
    o = Order.objects.create(order_no='O1')
    r = sc.delete(f'/api/orders/orders/{o.id}/')
    assert r.status_code == 403
    r2 = ac.delete(f'/api/orders/orders/{o.id}/')
    assert r2.status_code == 200

def test_only_admin_can_set_tracker(db, tracker_client, admin_client):
    tc, _ = tracker_client
    ac, _ = admin_client
    o = Order.objects.create(order_no='O1')
    new_tr = User.objects.create_user('tr2', password='pw123456')
    r = tc.post(f'/api/orders/orders/{o.id}/set-tracker/', {'tracker': new_tr.id}, format='json')
    assert r.status_code == 403
    r2 = ac.post(f'/api/orders/orders/{o.id}/set-tracker/', {'tracker': new_tr.id}, format='json')
    assert r2.status_code == 200
    assert Order.objects.get(pk=o.id).tracker == new_tr