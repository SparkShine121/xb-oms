import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from apps.finance.models import PaymentIn
from apps.orders.models import Order
from apps.basic_info.models import Customer


def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u


@pytest.fixture
def setup(db):
    s1 = _make_user('sales_a', 'salesman')
    s2 = _make_user('sales_b', 'salesman')
    ca = Customer.objects.create(name='客户甲', salesman=s1)
    cb = Customer.objects.create(name='客户乙', salesman=s2)
    oa = Order.objects.create(order_no='OA', tracking_status='排产', customer=ca, salesman=s1)
    ob = Order.objects.create(order_no='OB', tracking_status='排产', customer=cb, salesman=s2)
    p1 = PaymentIn.objects.create(order=oa, amount_usd='300.00', payment_date='2026-08-01', installment=1)
    p2 = PaymentIn.objects.create(order=ob, amount_usd='500.00', payment_date='2026-08-02', installment=1)
    return {'oa': oa, 'ob': ob, 'p1': p1, 'p2': p2, 's1': s1, 's2': s2}


def _client(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


# ---- CRUD ----

def test_admin_crud(db, setup):
    oa = setup['oa']
    c = _client(_make_user('adm', 'admin'))
    # create
    r = c.post('/api/finance/payments-in/',
               {'order': oa.id, 'amount_usd': '100.50', 'payment_date': '2026-08-10', 'installment': 2, 'note': '尾款'},
               format='json')
    assert r.status_code == 201
    assert r.data['data']['order_no'] == 'OA'
    assert r.data['data']['installment'] == 2
    pid = r.data['data']['id']
    # retrieve
    r = c.get(f'/api/finance/payments-in/{pid}/')
    assert r.status_code == 200 and r.data['data']['amount_usd'] == '100.50'
    # update
    r = c.patch(f'/api/finance/payments-in/{pid}/', {'amount_usd': '120.00'}, format='json')
    assert r.status_code == 200 and r.data['data']['amount_usd'] == '120.00'
    # delete
    r = c.delete(f'/api/finance/payments-in/{pid}/')
    assert r.status_code == 200
    assert PaymentIn.objects.count() == 2


def test_unauthenticated_denied(db, setup):
    c = _client()
    assert c.get('/api/finance/payments-in/').status_code == 401


# ---- 写权限 ----

def test_finance_can_write_not_delete(db, setup):
    fin = _make_user('fin', 'finance')
    c = _client(fin)
    r = c.post('/api/finance/payments-in/',
               {'order': setup['oa'].id, 'amount_usd': '88.00', 'payment_date': '2026-08-11'}, format='json')
    assert r.status_code == 201
    pid = r.data['data']['id']
    r = c.patch(f'/api/finance/payments-in/{pid}/', {'note': 'x'}, format='json')
    assert r.status_code == 200
    # destroy 仅 admin
    r = c.delete(f'/api/finance/payments-in/{pid}/')
    assert r.status_code == 403


def test_salesman_cannot_write(db, setup):
    c = _client(setup['s1'])
    r = c.post('/api/finance/payments-in/',
               {'order': setup['oa'].id, 'amount_usd': '1.00', 'payment_date': '2026-08-12'}, format='json')
    assert r.status_code == 403
    r = c.delete(f"/api/finance/payments-in/{setup['p1'].id}/")
    assert r.status_code == 403


def test_tracker_cannot_write(db, setup):
    t = _make_user('trk', 'tracker')
    setup['oa'].tracker = t
    setup['oa'].save()
    c = _client(t)
    r = c.post('/api/finance/payments-in/',
               {'order': setup['oa'].id, 'amount_usd': '1.00', 'payment_date': '2026-08-12'}, format='json')
    assert r.status_code == 403
    r = c.delete(f"/api/finance/payments-in/{setup['p1'].id}/")
    assert r.status_code == 403


# ---- 读数据范围 ----

def test_salesman_scoped_list(db, setup):
    """salesman 只能看自己客户的回款。"""
    c = _client(setup['s1'])
    r = c.get('/api/finance/payments-in/')
    assert r.status_code == 200
    ids = [i['id'] for i in r.data['data']['results']]
    assert ids == [setup['p1'].id]


def test_tracker_scoped_list(db, setup):
    """tracker 只能看派给自己订单的回款。"""
    t = _make_user('trk_x', 'tracker')
    setup['oa'].tracker = t
    setup['oa'].save()
    c = _client(t)
    r = c.get('/api/finance/payments-in/')
    assert r.status_code == 200
    ids = [i['id'] for i in r.data['data']['results']]
    assert ids == [setup['p1'].id]


def test_finance_sees_all(db, setup):
    fin = _make_user('fin_all', 'finance')
    c = _client(fin)
    r = c.get('/api/finance/payments-in/')
    assert len(r.data['data']['results']) == 2
