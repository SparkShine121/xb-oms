import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_factory(admin_client):
    r = admin_client.post('/api/basic-info/factories/', {
        'name': '华鑫', 'alias': '外部YT', 'contact': '张三', 'phone': '13800000000'
    }, format='json')
    assert r.status_code == 201 and r.data['data']['name'] == '华鑫'

def test_duplicate_name_rejected(admin_client):
    admin_client.post('/api/basic-info/factories/', {'name': '华鑫'}, format='json')
    r = admin_client.post('/api/basic-info/factories/', {'name': '华鑫'}, format='json')
    assert r.status_code == 400

def test_search_by_alias(admin_client):
    admin_client.post('/api/basic-info/factories/', {'name': '华鑫', 'alias': '外部YT'}, format='json')
    r = admin_client.get('/api/basic-info/factories/?search=外部YT')
    assert r.status_code == 200 and len(r.data['data']['results']) >= 1
