import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    return u

def test_login_returns_tokens(client, admin_user):
    r = client.post('/api/auth/login/', {'username': 'admin1', 'password': 'pw123456'}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data['data'] and 'refresh' in r.data['data']

def test_me_returns_user_and_roles(client, admin_user):
    client.force_authenticate(admin_user)
    r = client.get('/api/auth/me/')
    assert r.status_code == 200
    assert r.data['data']['username'] == 'admin1'
    assert 'admin' in r.data['data']['roles']

def test_create_groups_command(db):
    from django.core.management import call_command
    call_command('create_groups')
    assert Group.objects.filter(name='admin').exists()
    assert Group.objects.filter(name='salesman').exists()
    assert Group.objects.filter(name='tracker').exists()
    assert Group.objects.filter(name='finance').exists()
