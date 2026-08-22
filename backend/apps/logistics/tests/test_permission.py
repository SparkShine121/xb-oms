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


# ---- 数据范围（get_queryset 角色过滤）防护测试 ----

def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u

def test_salesman_scoped_list(db, setup):
    """salesman 只能看到自己客户的物流单，看不到其他 salesman 客户的。"""
    s1 = _make_user('sc_a', 'salesman')
    s2 = _make_user('sc_b', 'salesman')
    ca = Customer.objects.create(name='客户甲', salesman=s1)
    cb = Customer.objects.create(name='客户乙', salesman=s2)
    oa = Order.objects.create(order_no='OSA', tracking_status='排产', customer=ca)
    ob = Order.objects.create(order_no='OSB', tracking_status='排产', customer=cb)
    Logistics.objects.create(order=oa, tracking_no='A001')
    Logistics.objects.create(order=ob, tracking_no='B001')

    c = APIClient(); c.force_authenticate(s1)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    order_nos = [i['order_no'] for i in r.data['data']['results']]
    assert order_nos == ['OSA']  # 只见自己客户的

def test_tracker_scoped_list(db, setup):
    """tracker 只能看到派给自己的订单的物流单。"""
    t1 = _make_user('tk_a', 'tracker')
    t2 = _make_user('tk_b', 'tracker')
    o1 = Order.objects.create(order_no='OT1', tracking_status='排产',
                              customer=Customer.objects.create(name='客户丙'), tracker=t1)
    o2 = Order.objects.create(order_no='OT2', tracking_status='排产',
                              customer=Customer.objects.create(name='客户丁'), tracker=t2)
    Logistics.objects.create(order=o1, tracking_no='T001')
    Logistics.objects.create(order=o2, tracking_no='T002')

    c = APIClient(); c.force_authenticate(t1)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    order_nos = [i['order_no'] for i in r.data['data']['results']]
    assert order_nos == ['OT1']  # 只见派给自己的


# ---- 删除仅 admin、tracker 更新 ----

def test_delete_admin_only(db, setup, tracker_client, salesman_client):
    tc, tr = tracker_client
    url = f'/api/logistics/shipments/{setup["logistics"].id}/'
    r = tc.delete(url)
    assert r.status_code == 403
    r2 = salesman_client.delete(url)
    assert r2.status_code == 403

def test_tracker_can_update_own(db, setup, tracker_client):
    tc, tr = tracker_client
    setup['order'].tracker = tr; setup['order'].save()
    r = tc.patch(f'/api/logistics/shipments/{setup["logistics"].id}/',
                 {'tracking_no': 'PATCHED'}, format='json')
    assert r.status_code == 200
    assert r.data['data']['tracking_no'] == 'PATCHED'
