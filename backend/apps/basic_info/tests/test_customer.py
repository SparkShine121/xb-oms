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
    sales.groups.add(Group.objects.get(name='salesman'))
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

# ---- BUG-SIM-007: 客户名全局唯一 ----

def test_duplicate_customer_name_rejected(admin_client, db):
    admin_client.post('/api/basic-info/customers/', {'name': '张三'}, format='json')
    r = admin_client.post('/api/basic-info/customers/', {'name': '张三'}, format='json')
    assert r.status_code == 400

def test_customer_name_unique_allows_update_self(admin_client, db):
    """更新自身（改其他字段）不触发同名误判"""
    r = admin_client.post('/api/basic-info/customers/', {'name': '李四'}, format='json')
    cid = r.data['data']['id']
    r2 = admin_client.patch(f'/api/basic-info/customers/{cid}/', {'phone': '123'}, format='json')
    assert r2.status_code == 200

def test_import_match_customer_still_works(db):
    """唯一约束不破坏导入匹配（同名消歧后匹配确定）"""
    from apps.orders.importers import _match_customer
    from apps.basic_info.models import Customer
    Customer.objects.create(name='吴芳')
    assert _match_customer('吴芳') is not None
    assert _match_customer('不存在') is None

# ---- BUG-SIM-007 回归锁：DB 层约束兜底 + 统一异常映射 ----

def test_customer_name_db_constraint(db):
    """绕过 serializer 直写 DB 也被唯一约束拦截"""
    from django.db import IntegrityError, transaction as dj_transaction
    from apps.basic_info.models import Customer
    Customer.objects.create(name='独苗')
    with pytest.raises(IntegrityError):
        with dj_transaction.atomic():
            Customer.objects.create(name='独苗')

def test_integrity_error_maps_to_400():
    """并发撞唯一约束产生的 IntegrityError 统一映射为 400（原为裸 500）"""
    from django.db import IntegrityError
    from common.exceptions import custom_exception_handler
    resp = custom_exception_handler(IntegrityError('UNIQUE constraint failed'), None)
    assert resp.status_code == 400 and resp.data['code'] == 1001
