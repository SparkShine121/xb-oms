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

# ---- BUG-SIM-018: 登录限流（按 IP） ----

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _login(client, pw='bad'):
    return client.post('/api/auth/login/', {'username': 'lockuser', 'password': pw}, format='json')


def test_login_lockout_after_5_failures(db):
    User.objects.create_user('lockuser', password='right123')
    c = APIClient()
    for i in range(5):
        r = _login(c)
        assert r.status_code == 401, i
    r6 = _login(c)
    assert r6.status_code == 429  # 锁定
    r7 = _login(c, 'right123')
    assert r7.status_code == 429  # 正确密码在锁定窗口内同样拒绝


def test_login_success_resets_counter(db):
    User.objects.create_user('lockuser', password='right123')
    c = APIClient()
    for i in range(4):
        assert _login(c).status_code == 401
    assert _login(c, 'right123').status_code == 200  # 成功清零
    for i in range(4):
        assert _login(c).status_code == 401
    assert _login(c).status_code == 401  # 第 5 次失败（未超）
    assert _login(c).status_code == 429  # 第 6 次锁定

# ---- BUG-SIM-019: access 寿命 30 分钟 ----

def test_access_token_lifetime_30min():
    from django.conf import settings
    from datetime import timedelta
    assert settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] == timedelta(minutes=30)
