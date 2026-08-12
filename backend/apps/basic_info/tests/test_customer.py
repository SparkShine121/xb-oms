import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_customer_with_salesman(admin_client, db):
    sales = User.objects.create_user('sales1', password='pw123456')
    r = admin_client.post('/api/basic-info/customers/', {
        'name': '客户A', 'contact_person': '王五', 'salesman': sales.id
    }, format='json')
    assert r.status_code == 201 and r.data['data']['salesman'] == sales.id

def test_filter_by_salesman(admin_client, db):
    s1 = User.objects.create_user('sales1', password='pw123456')
    s2 = User.objects.create_user('sales2', password='pw123456')
    admin_client.post('/api/basic-info/customers/', {'name': 'A', 'salesman': s1.id}, format='json')
    admin_client.post('/api/basic-info/customers/', {'name': 'B', 'salesman': s2.id}, format='json')
    r = admin_client.get(f'/api/basic-info/customers/?salesman={s1.id}')
    assert r.status_code == 200
    assert all(c['salesman'] == s1.id for c in r.data['data']['results'])
