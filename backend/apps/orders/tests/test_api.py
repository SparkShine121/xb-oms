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
