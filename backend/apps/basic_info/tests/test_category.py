import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_category(admin_client):
    r = admin_client.post('/api/basic-info/categories/', {'name': '包装类'}, format='json')
    assert r.status_code == 201 and r.data['data']['name'] == '包装类'

def test_tree(admin_client):
    parent = admin_client.post('/api/basic-info/categories/', {'name': '包装类'}, format='json').data['data']
    admin_client.post('/api/basic-info/categories/', {'name': '手提袋', 'parent': parent['id']}, format='json')
    r = admin_client.get('/api/basic-info/categories/tree/')
    assert r.status_code == 200
    tree = r.data['data']
    assert any(c['name'] == '包装类' and any(ch['name'] == '手提袋' for ch in c['children']) for c in tree)

def test_non_admin_cannot_write(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/basic-info/categories/', {'name': 'X'}, format='json')
    assert r.status_code == 403

def test_filter_by_parent(admin_client):
    parent = admin_client.post('/api/basic-info/categories/', {'name': '包装类'}, format='json').data['data']
    admin_client.post('/api/basic-info/categories/', {'name': '手提袋', 'parent': parent['id']}, format='json')
    r = admin_client.get(f'/api/basic-info/categories/?parent={parent["id"]}')
    assert r.status_code == 200
    results = r.data['data']['results']
    assert len(results) == 1 and results[0]['name'] == '手提袋'

def test_search_by_name(admin_client):
    admin_client.post('/api/basic-info/categories/', {'name': '包装类'}, format='json')
    admin_client.post('/api/basic-info/categories/', {'name': '印刷类'}, format='json')
    r = admin_client.get('/api/basic-info/categories/?search=包装')
    assert r.status_code == 200
    results = r.data['data']['results']
    assert len(results) == 1 and results[0]['name'] == '包装类'
