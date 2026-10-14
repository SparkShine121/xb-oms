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

# ---- BUG-SIM-021/028: 删用户保护 + 停用 ----
from rest_framework.test import APIClient
from apps.basic_info.models import Customer


def _mk(role='salesman', name=None):
    u = User.objects.create_user(name or f'u_{role}_{User.objects.count()}', password='pw123456')
    u.groups.add(Group.objects.get(name=role))
    return u


def _admin():
    return _mk('admin', f'adm_{User.objects.count()}')


def test_delete_self_rejected(db):
    u = _admin()
    c = APIClient(); c.force_authenticate(u)
    r = c.delete(f'/api/auth/users/{u.id}/')
    assert r.status_code == 400


def test_delete_last_admin_rejected(db):
    u = _admin()
    c = APIClient(); c.force_authenticate(u)
    r = c.delete(f'/api/auth/users/{u.id}/')
    assert r.status_code == 400  # 防自删已覆盖唯一 admin；两 admin 时可删其一
    u2 = _admin()
    r2 = c.delete(f'/api/auth/users/{u2.id}/')
    assert r2.status_code == 200  # 两个 admin 删一个 OK


def test_delete_user_with_data_requires_transfer(db):
    adm = _admin()
    target = _mk('salesman', 'sales_del')
    Customer.objects.create(name='C1', salesman=target)
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/')
    assert r.status_code == 400  # 未指定承接人
    # 指定承接人 → 成功且转移
    to = _mk('salesman', 'sales_recv')
    r2 = c.delete(f'/api/auth/users/{target.id}/', {'transfer_to': to.id}, format='json')
    assert r2.status_code == 200
    assert not User.objects.filter(pk=target.id).exists()
    cust = Customer.objects.get(name='C1')
    assert cust.salesman_id == to.id


def test_delete_transfers_order_tracker_role_aware(db):
    adm = _admin()
    target = _mk('salesman', 'sales_del2')
    to = _mk('salesman', 'sales_recv2')  # 非 tracker 角色
    tr = _mk('tracker', 'tr_recv')
    from apps.orders.models import Order
    o1 = Order.objects.create(order_no='OD1', salesman=target, tracker=target)
    o2 = Order.objects.create(order_no='OD2', salesman=target)
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/', {'transfer_to': to.id}, format='json')
    assert r.status_code == 200
    o1.refresh_from_db(); o2.refresh_from_db()
    assert o1.salesman_id == to.id
    assert o1.tracker_id is None  # 承接人非 tracker → 置空待重新派单（014 语义）
    assert o2.salesman_id == to.id and o2.tracker_id is None
    assert tr.groups.filter(name="tracker").exists()  # sanity

def test_delete_user_without_data_no_transfer_needed(db):
    adm = _admin()
    target = _mk('salesman', 'sales_nodata')
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/')
    assert r.status_code == 200

def test_transfer_to_self_rejected(db):
    adm = _admin()
    target = _mk('salesman', 'sales_tself')
    Customer.objects.create(name='CX', salesman=target)
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/', {'transfer_to': target.id}, format='json')
    assert r.status_code == 400

# ---- BUG-SIM-028: 停用 ----

def test_deactivate_via_serializer(db, admin_client):
    target = _mk('salesman', 'sales_deact')
    r = admin_client.patch(f'/api/auth/users/{target.id}/', {'is_active': False}, format='json')
    assert r.status_code == 200
    assert User.objects.get(pk=target.id).is_active is False
    r2 = admin_client.patch(f'/api/auth/users/{target.id}/', {'is_active': True}, format='json')
    assert User.objects.get(pk=target.id).is_active is True


def test_deactivated_login_rejected(db):
    u = _mk('salesman', 'sales_off')
    u.is_active = False; u.save()
    c = APIClient()
    r = c.post('/api/auth/login/', {'username': u.username, 'password': 'pw123456'}, format='json')
    assert r.status_code == 401


def test_deactivated_access_token_immediate_401(db):
    """simplejwt get_user 对 is_active=False 即刻拒绝（快于 access 自然过期）"""
    u = _mk('salesman', 'sales_off2')
    c = APIClient()
    login = c.post('/api/auth/login/', {'username': u.username, 'password': 'pw123456'}, format='json')
    assert login.status_code == 200
    access = login.data['data']['access']
    u.is_active = False; u.save()
    auth = APIClient(); auth.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r = auth.get('/api/auth/me/')
    assert r.status_code == 401


def test_deactivate_blacklists_refresh(db):
    u = _mk('salesman', 'sales_off3')
    c = APIClient()
    login = c.post('/api/auth/login/', {'username': u.username, 'password': 'pw123456'}, format='json')
    refresh = login.data['data']['refresh']
    adm = _admin()
    ac = APIClient(); ac.force_authenticate(adm)
    assert ac.patch(f'/api/auth/users/{u.id}/', {'is_active': False}, format='json').status_code == 200
    r = c.post('/api/auth/refresh/', {'refresh': refresh}, format='json')
    assert r.status_code == 401  # refresh 已被 blacklist

# ---- BUG-SIM-021/028 followup（旁观者审查 fail 项）----

def test_user_bulk_delete_blocked(db):
    """用户不支持批量删除（transfer_to 无法按 id 表达；防自删/末位admin/承接人守卫不可绕过）"""
    adm = _admin()
    target = _mk('salesman', 'sales_bd')
    c = APIClient(); c.force_authenticate(adm)
    r = c.post('/api/auth/users/bulk-delete/', {'ids': [target.id, adm.id]}, format='json')
    assert r.status_code == 400
    assert User.objects.filter(pk__in=[target.id, adm.id]).count() == 2


def test_deactivate_last_admin_rejected(db, admin_client):
    u = _admin()
    User.objects.filter(username='admin1').update(is_active=False)  # 夹具自带 admin 置非活跃（force_authenticate 仍可用）
    r = admin_client.patch(f'/api/auth/users/{u.id}/', {'is_active': False}, format='json')
    assert r.status_code == 400  # u 是最后一个活跃 admin
    assert User.objects.get(pk=u.id).is_active is True


def test_self_deactivate_rejected(db):
    u = _admin()
    c = APIClient(); c.force_authenticate(u)
    r = c.patch(f'/api/auth/users/{u.id}/', {'is_active': False}, format='json')
    assert r.status_code == 400


def test_deactivate_actually_blacklists_tokens(db, admin_client):
    u = _mk('salesman', 'sales_bl')
    c = APIClient()
    login = c.post('/api/auth/login/', {'username': u.username, 'password': 'pw123456'}, format='json')
    refresh = login.data['data']['refresh']
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    assert admin_client.patch(f'/api/auth/users/{u.id}/', {'is_active': False}, format='json').status_code == 200
    assert BlacklistedToken.objects.filter(token__user=u).exists()  # 真·拉黑（非 is_active 规则兜底的假绿）


def test_transfer_to_non_int_rejected(db):
    adm = _admin()
    target = _mk('salesman', 'sales_nint')
    Customer.objects.create(name='CN', salesman=target)
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/', {'transfer_to': 'abc'}, format='json')
    assert r.status_code == 400


def test_delete_transfers_customer_tracker_by_role(db):
    """Customer.tracker 同 Order.tracker 规则：被删者是 tracker 时按承接人角色转移或置空"""
    adm = _admin()
    target = _mk('tracker', 'sales_ct')  # 被删者本身是 tracker（名下客户 tracker 指向他）
    to = _mk('salesman', 'sales_ct2')    # 承接人非 tracker → tracker 置空
    cust = Customer.objects.create(name='CT', salesman=target, tracker=target)
    c = APIClient(); c.force_authenticate(adm)
    r = c.delete(f'/api/auth/users/{target.id}/', {'transfer_to': to.id}, format='json')
    assert r.status_code == 200
    cust.refresh_from_db()
    assert cust.salesman_id == to.id
    assert cust.tracker_id is None  # 承接人非 tracker → 置空
