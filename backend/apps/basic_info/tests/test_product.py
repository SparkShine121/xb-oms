import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_product(admin_client):
    r = admin_client.post('/api/basic-info/products/', {
        'product_no': 'P001', 'model': 'M1', 'name': '名片',
        'spec': '90x54mm', 'default_price': '0.10', 'default_cost_price': '0.50'
    }, format='json')
    assert r.status_code == 201 and r.data['data']['product_no'] == 'P001'

def test_duplicate_product_no_rejected(admin_client):
    payload = {'product_no': 'P002', 'model': 'M', 'name': 'X'}
    admin_client.post('/api/basic-info/products/', payload, format='json')
    r = admin_client.post('/api/basic-info/products/', payload, format='json')
    assert r.status_code == 400

def test_filter_by_category(admin_client, db):
    from apps.basic_info.models import Category
    cat = Category.objects.create(name='C1')
    admin_client.post('/api/basic-info/products/', {'product_no': 'P1', 'name': 'a', 'category': cat.id}, format='json')
    r = admin_client.get(f'/api/basic-info/products/?category={cat.id}')
    assert r.status_code == 200 and len(r.data['data']['results']) >= 1
