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
def tracker_client(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    u.groups.add(Group.objects.get(name='tracker'))
    c = APIClient(); c.force_authenticate(u); return c, u

@pytest.fixture
def finance_client(db):
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u); return c, u

def test_tracker_advance_own_order(db, tracker_client):
    c, tr = tracker_client
    o = Order.objects.create(order_no='O1', tracking_status='接单', tracker=tr)
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracking_status == '排产'

def test_tracker_cannot_advance_other(db, tracker_client):
    c, _ = tracker_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')  # 无 tracker
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r.status_code == 403

def test_finance_readonly_timeline(db, finance_client):
    c, _ = finance_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    r = c.get(f'/api/tracking/orders/{o.id}/timeline/')
    assert r.status_code == 200
    r2 = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r2.status_code == 403

def test_admin_advance_any(db, admin_client):
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='排产')
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracking_status == '生产中'

def test_reject_at_first_node_forbidden(db, tracker_client):
    c, tr = tracker_client
    o = Order.objects.create(order_no='O1', tracking_status='接单', tracker=tr)
    r = c.post(f'/api/tracking/orders/{o.id}/reject/', {'note': '驳回'}, format='multipart')
    assert r.status_code == 400  # 接单不可驳回

def test_advance_at_last_node_forbidden(db, tracker_client):
    c, tr = tracker_client
    o = Order.objects.create(order_no='O1', tracking_status='回款', tracker=tr)
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r.status_code == 400  # 回款终态不可推进

def test_cancelled_order_no_flow(db, tracker_client):
    c, tr = tracker_client
    o = Order.objects.create(order_no='O1', tracking_status='已取消', tracker=tr, is_cancelled=True)
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    assert r.status_code == 400
