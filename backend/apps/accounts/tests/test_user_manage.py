import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_admin_creates_salesman(admin_client, db):
    r = admin_client.post('/api/auth/users/', {
        'username': 'sales_new', 'password': 'pw123456', 'groups': ['salesman']
    }, format='json')
    assert r.status_code == 201
    assert Group.objects.get(name='salesman') in User.objects.get(username='sales_new').groups.all()

def test_non_admin_cannot_access(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u)
    r = c.get('/api/auth/users/')
    assert r.status_code == 403
