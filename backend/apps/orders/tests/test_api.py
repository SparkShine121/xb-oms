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