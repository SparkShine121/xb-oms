import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_domestic(admin_client):
    r = admin_client.post('/api/basic-info/logistics/', {
        'name': '圆通', 'type': 'domestic', 'contact': '李四'
    }, format='json')
    assert r.status_code == 201 and r.data['data']['type'] == 'domestic'

def test_invalid_type_rejected(admin_client):
    r = admin_client.post('/api/basic-info/logistics/', {'name': 'X', 'type': 'space'}, format='json')
    assert r.status_code == 400

def test_filter_by_type(admin_client):
    admin_client.post('/api/basic-info/logistics/', {'name': 'DHL', 'type': 'international'}, format='json')
    r = admin_client.get('/api/basic-info/logistics/?type=international')
    assert r.status_code == 200 and len(r.data['data']['results']) >= 1
