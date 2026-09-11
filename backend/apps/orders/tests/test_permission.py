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
# ---- BUG-SIM-001: bulk-delete 权限必须等价于单条删除 ----

def test_salesman_cannot_bulk_delete_orders(db, sales_client):
    sc, sales = sales_client
    cust = Customer.objects.create(name='C1', salesman=sales)
    o = Order.objects.create(order_no='O1', customer=cust)
    r = sc.post('/api/orders/orders/bulk-delete/', {'ids': [o.id]}, format='json')
    assert r.status_code == 403
    assert Order.objects.filter(id=o.id).exists()

def test_tracker_cannot_bulk_delete_orders(db, tracker_client):
    tc, tr = tracker_client
    o = Order.objects.create(order_no='O1', tracker=tr)
    r = tc.post('/api/orders/orders/bulk-delete/', {'ids': [o.id]}, format='json')
    assert r.status_code == 403
    assert Order.objects.filter(id=o.id).exists()

def test_finance_cannot_bulk_delete_orders(db):
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u)
    o = Order.objects.create(order_no='O1')
    r = c.post('/api/orders/orders/bulk-delete/', {'ids': [o.id]}, format='json')
    assert r.status_code == 403
    assert Order.objects.filter(id=o.id).exists()

def test_admin_can_bulk_delete_orders(db, admin_client):
    ac, _ = admin_client
    o1 = Order.objects.create(order_no='O1'); o2 = Order.objects.create(order_no='O2')
    r = ac.post('/api/orders/orders/bulk-delete/', {'ids': [o1.id, o2.id]}, format='json')
    assert r.status_code == 200
    assert r.data['data']['deleted'] == 2
    assert not Order.objects.filter(id__in=[o1.id, o2.id]).exists()

def test_finance_bulk_delete_mixed_reports_lists(db):
    """finance 禁删 + 不存在 id 混合：不删任何记录，逐条报告清单（BUG-SIM-025 同修）"""
    u = User.objects.create_user('fin2', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u)
    o = Order.objects.create(order_no='O1')
    r = c.post('/api/orders/orders/bulk-delete/', {'ids': [o.id, 99999]}, format='json')
    assert r.status_code == 200
    body = r.data['data']
    assert body['deleted'] == 0
    assert body['forbidden'] == [o.id]
    assert body['not_found'] == [99999]
    assert Order.objects.filter(id=o.id).exists()
