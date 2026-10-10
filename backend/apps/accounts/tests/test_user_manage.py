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

def test_admin_updates_user_password(admin_client, db):
    target = User.objects.create_user('target1', password='old123456')
    r = admin_client.patch(f'/api/auth/users/{target.id}/', {
        'password': 'new123456'
    }, format='json')
    assert r.status_code == 200
    assert User.objects.get(id=target.id).check_password('new123456')

def test_admin_updates_user_groups(admin_client, db):
    """角色单选:更新时把用户角色切换为单个角色组"""
    target = User.objects.create_user('target2', password='pw123456')
    target.groups.add(Group.objects.get(name='salesman'))
    r = admin_client.patch(f'/api/auth/users/{target.id}/', {
        'groups': ['tracker']
    }, format='json')
    assert r.status_code == 200
    groups = set(User.objects.get(id=target.id).groups.values_list('name', flat=True))
    assert groups == {'tracker'}

def test_user_cannot_have_multiple_roles(admin_client, db):
    """角色单选：一次分配多个角色组应被拒绝"""
    from apps.accounts.serializers import UserManageSerializer
    from apps.accounts.serializers import Group
    s = UserManageSerializer(data={'username': 'multi', 'password': 'pw123456',
                                   'groups': ['admin', 'tracker']})
    assert not s.is_valid(), s.errors
    assert '每个用户只能分配一个角色' in str(s.errors)

# ---- BUG-SIM-001: bulk-delete 权限必须等价于单条删除（回归锁定） ----

def test_non_admin_cannot_bulk_delete_users(db):
    u = User.objects.create_user('sales3', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    target = User.objects.create_user('victim', password='pw123456')
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/auth/users/bulk-delete/', {'ids': [target.id]}, format='json')
    assert r.status_code == 403
    assert User.objects.filter(id=target.id).exists()

# ---- BUG-SIM-020: 密码强度 + 弱密码标记 ----

@pytest.mark.parametrize('weak', ['1', '12345678', 'abcdefgh'])
def test_create_user_weak_password_rejected(admin_client, db, weak):
    r = admin_client.post('/api/auth/users/', {'username': 'w1', 'password': weak, 'groups': ['salesman']}, format='json')
    assert r.status_code == 400

def test_create_user_strong_password_ok(admin_client, db):
    r = admin_client.post('/api/auth/users/', {'username': 's1', 'password': 'good1234', 'groups': ['salesman']}, format='json')
    assert r.status_code == 201

def test_update_password_weak_rejected(admin_client, db):
    target = User.objects.create_user('t_weak', password='old12345')
    r = admin_client.patch(f'/api/auth/users/{target.id}/', {'password': '12345678'}, format='json')
    assert r.status_code == 400

def test_weak_password_flag_in_list(admin_client, db):
    # aa1234 不满足策略，经 API 建号会被 400 拦——弱密码只能经 ORM/脚本产生（过渡态），故直建后补标记
    from apps.accounts.serializers import mark_password_flag
    u1 = User.objects.create_user('flag_weak', password='aa1234')
    mark_password_flag(u1, 'aa1234')  # 与重置脚本同路径
    User.objects.create_user('flag_strong', password='good1234')  # 无标记记录 → False
    r = admin_client.get('/api/auth/users/')
    flags = {u['username']: u.get('is_weak_password') for u in r.data['data']['results']}
    assert flags['flag_weak'] is True
    assert flags['flag_strong'] is False

# ---- 个人改密（连带补充） ----

def test_change_password_wrong_old_rejected(db):
    from rest_framework.test import APIClient
    u = User.objects.create_user('me_chg', password='old12345')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/auth/me/change-password/', {'old_password': 'wrong', 'new_password': 'good1234'}, format='json')
    assert r.status_code == 401

def test_change_password_weak_new_rejected(db):
    from rest_framework.test import APIClient
    u = User.objects.create_user('me_chg2', password='old12345')
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/auth/me/change-password/', {'old_password': 'old12345', 'new_password': '12345678'}, format='json')
    assert r.status_code == 400

def test_change_password_ok(db):
    from rest_framework.test import APIClient
    u = User.objects.create_user('me_chg3', password='old12345')
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/auth/me/change-password/', {'old_password': 'old12345', 'new_password': 'good1234'}, format='json')
    assert r.status_code == 200
    assert User.objects.get(pk=u.pk).check_password('good1234')
