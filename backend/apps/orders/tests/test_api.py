import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order
from io import BytesIO

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_order(admin_client, db):
    r = admin_client.post('/api/orders/orders/', {'order_no':'O1','amount_usd':'100','items':[]}, format='json')
    assert r.status_code == 201 and r.data['data']['order_no'] == 'O1'

def test_import_action_bad_file(admin_client, db):
    f = BytesIO(b'not xlsx'); f.name = 'bad.xlsx'
    r = admin_client.post('/api/orders/orders/import/', {'file': f}, format='multipart')
    assert r.status_code == 400  # 坏文件容错

def test_import_template_download(admin_client, db):
    r = admin_client.get('/api/orders/orders/import-template/')
    assert r.status_code == 200

def test_exchange_rate_crud_admin(admin_client, db):
    r = admin_client.post('/api/orders/exchange-rates/', {'currency_pair':'USD/CNY','rate':'7.20','effective_date':'2026-08-01'}, format='json')
    assert r.status_code == 201
    r2 = admin_client.get('/api/orders/exchange-rates/')
    assert r2.status_code == 200

def test_exchange_rate_non_admin_forbidden(db):
    from django.contrib.auth.models import User, Group
    u = User.objects.create_user('sales1', password='pw123456'); u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/orders/exchange-rates/', {'currency_pair':'USD/CNY','rate':'7.20','effective_date':'2026-08-01'}, format='json')
    assert r.status_code == 403
def test_salesman_cannot_change_salesman_on_update(db):
    """非 admin 更新订单时,派单字段(salesman/tracker)应被忽略——仅 admin 可改"""
    from apps.basic_info.models import Customer
    admin = User.objects.create_user('admin2', password='pw123456')
    admin.groups.add(Group.objects.get(name='admin'))
    sales1 = User.objects.create_user('salesA', password='pw123456')
    sales1.groups.add(Group.objects.get(name='salesman'))
    sales2 = User.objects.create_user('salesB', password='pw123456')
    sales2.groups.add(Group.objects.get(name='salesman'))
    cust = Customer.objects.create(name='客户甲', salesman=sales1)
    order = Order.objects.create(order_no='OO1', customer=cust, salesman=sales1)
    client = APIClient(); client.force_authenticate(sales1)
    r = client.patch(f'/api/orders/orders/{order.id}/',
                     {'remark': '业务员改备注', 'salesman': sales2.id}, format='json')
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.salesman_id == sales1.id      # salesman 变更被忽略
    assert order.remark == '业务员改备注'        # 其他字段正常更新
    # admin 可以改
    cadmin = APIClient(); cadmin.force_authenticate(admin)
    r2 = cadmin.patch(f'/api/orders/orders/{order.id}/', {'salesman': sales2.id}, format='json')
    assert r2.status_code == 200
    order.refresh_from_db()
    assert order.salesman_id == sales2.id      # admin 修改生效

# ---- BUG-SIM-002: 挂结算订单删除保护（Q5:i）----
from apps.basic_info.models import Customer
from apps.basic_info.models import Factory as OrderFactory
from apps.orders.models import OrderItem
from apps.factory_payment.models import FactoryPayment


def _make_orders_with_settlement():
    f = OrderFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='C1')
    o_settled = Order.objects.create(order_no='OS', customer=c)
    item = OrderItem.objects.create(order=o_settled, seq=1, product_no='P1', qty=1, subtotal='100', cost_price='72')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    o_plain = Order.objects.create(order_no='OP', customer=c)
    OrderItem.objects.create(order=o_plain, seq=1, product_no='P9', qty=1, subtotal='50', cost_price='36')
    return o_settled, o_plain


def test_destroy_order_with_settlement_rejected(db, admin_client):
    o_settled, _ = _make_orders_with_settlement()
    r = admin_client.delete(f'/api/orders/orders/{o_settled.id}/')
    assert r.status_code == 400
    assert Order.objects.filter(id=o_settled.id).exists()
    assert FactoryPayment.objects.count() == 1


def test_destroy_order_without_settlement_ok(db, admin_client):
    _, o_plain = _make_orders_with_settlement()
    r = admin_client.delete(f'/api/orders/orders/{o_plain.id}/')
    assert r.status_code == 200
    assert not Order.objects.filter(id=o_plain.id).exists()


def test_bulk_delete_mixed_settlement_reports_forbidden(db, admin_client):
    o_settled, o_plain = _make_orders_with_settlement()
    r = admin_client.post('/api/orders/orders/bulk-delete/', {'ids': [o_settled.id, o_plain.id]}, format='json')
    assert r.status_code == 200
    assert r.data['data']['deleted'] == 1
    assert r.data['data']['forbidden'] == [o_settled.id]
    assert Order.objects.filter(id=o_settled.id).exists()
    assert FactoryPayment.objects.count() == 1

# ---- BUG-SIM-012: 汇率 rate>0 校验 ----

def test_exchange_rate_non_positive_rejected(db, admin_client):
    for bad in ('0', '-7.2'):
        r = admin_client.post('/api/orders/exchange-rates/',
                              {'currency_pair': 'USD/CNY', 'rate': bad, 'effective_date': '2026-09-17'}, format='json')
        assert r.status_code == 400, bad

# ---- BUG-SIM-007: 汇率 (币种对, 日期) 唯一 ----

def test_duplicate_exchange_rate_rejected(db, admin_client):
    r1 = admin_client.post('/api/orders/exchange-rates/',
                           {'currency_pair': 'USD/CNY', 'rate': '7.2', 'effective_date': '2026-09-01'}, format='json')
    assert r1.status_code == 201
    r2 = admin_client.post('/api/orders/exchange-rates/',
                           {'currency_pair': 'USD/CNY', 'rate': '7.5', 'effective_date': '2026-09-01'}, format='json')
    assert r2.status_code == 400

def test_same_pair_different_date_allowed(db, admin_client):
    r = admin_client.post('/api/orders/exchange-rates/',
                          {'currency_pair': 'USD/CNY', 'rate': '7.5', 'effective_date': '2026-10-01'}, format='json')
    assert r.status_code == 201

def test_same_date_different_pair_allowed(db, admin_client):
    r = admin_client.post('/api/orders/exchange-rates/',
                          {'currency_pair': 'EUR/CNY', 'rate': '7.9', 'effective_date': '2026-09-01'}, format='json')
    assert r.status_code == 201
