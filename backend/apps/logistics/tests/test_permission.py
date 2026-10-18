import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.logistics.models import Logistics
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, LogisticsProvider, Customer

@pytest.fixture
def setup(db):
    carrier = LogisticsProvider.objects.create(name='圆通', type='domestic')
    intl = LogisticsProvider.objects.create(name='DHL', type='international')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    logi = Logistics.objects.create(order=o, domestic_carrier=carrier, intl_method=intl, tracking_no='YT123', cost='50.00')
    return {'logistics': logi, 'order': o, 'carrier': carrier, 'intl': intl}

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def tracker_client(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    u.groups.add(Group.objects.get(name='tracker'))
    c = APIClient(); c.force_authenticate(u); return c, u

@pytest.fixture
def salesman_client(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u); return c

def test_admin_crud(db, setup, admin_client):
    r = admin_client.get('/api/logistics/shipments/')
    assert r.status_code == 200 and len(r.data['data']['results']) >= 1
    r2 = admin_client.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'NEW'}, format='json')
    assert r2.status_code == 201
    r3 = admin_client.delete(f'/api/logistics/shipments/{setup["logistics"].id}/')
    assert r3.status_code == 200

def test_tracker_can_write_own(db, setup, tracker_client):
    tc, tr = tracker_client
    from django.contrib.auth.models import User
    setup['order'].tracker = tr; setup['order'].save()
    r = tc.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'TRK'}, format='json')
    assert r.status_code == 201

def test_salesman_readonly_scoped(db, setup, salesman_client):
    sc = salesman_client
    r = sc.get('/api/logistics/shipments/')
    assert r.status_code == 200  # 能看
    r2 = sc.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'X'}, format='json')
    assert r2.status_code == 403  # 不能写

def test_finance_readonly(db, setup):
    from django.contrib.auth.models import User, Group
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    r2 = c.post('/api/logistics/shipments/', {'order': setup['order'].id, 'tracking_no': 'X'}, format='json')
    assert r2.status_code == 403


# ---- 数据范围（get_queryset 角色过滤）防护测试 ----

def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u

def test_salesman_scoped_list(db, setup):
    """salesman 只能看到自己客户的物流单，看不到其他 salesman 客户的。"""
    s1 = _make_user('sc_a', 'salesman')
    s2 = _make_user('sc_b', 'salesman')
    ca = Customer.objects.create(name='客户甲', salesman=s1)
    cb = Customer.objects.create(name='客户乙', salesman=s2)
    oa = Order.objects.create(order_no='OSA', tracking_status='排产', customer=ca)
    ob = Order.objects.create(order_no='OSB', tracking_status='排产', customer=cb)
    Logistics.objects.create(order=oa, tracking_no='A001')
    Logistics.objects.create(order=ob, tracking_no='B001')

    c = APIClient(); c.force_authenticate(s1)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    order_nos = [i['order_no'] for i in r.data['data']['results']]
    assert order_nos == ['OSA']  # 只见自己客户的

def test_tracker_scoped_list(db, setup):
    """tracker 只能看到派给自己的订单的物流单。"""
    t1 = _make_user('tk_a', 'tracker')
    t2 = _make_user('tk_b', 'tracker')
    o1 = Order.objects.create(order_no='OT1', tracking_status='排产',
                              customer=Customer.objects.create(name='客户丙'), tracker=t1)
    o2 = Order.objects.create(order_no='OT2', tracking_status='排产',
                              customer=Customer.objects.create(name='客户丁'), tracker=t2)
    Logistics.objects.create(order=o1, tracking_no='T001')
    Logistics.objects.create(order=o2, tracking_no='T002')

    c = APIClient(); c.force_authenticate(t1)
    r = c.get('/api/logistics/shipments/')
    assert r.status_code == 200
    order_nos = [i['order_no'] for i in r.data['data']['results']]
    assert order_nos == ['OT1']  # 只见派给自己的


# ---- 删除仅 admin、tracker 更新 ----

def test_delete_admin_only(db, setup, tracker_client, salesman_client):
    tc, tr = tracker_client
    url = f'/api/logistics/shipments/{setup["logistics"].id}/'
    r = tc.delete(url)
    assert r.status_code == 403
    r2 = salesman_client.delete(url)
    assert r2.status_code == 403

def test_tracker_can_update_own(db, setup, tracker_client):
    tc, tr = tracker_client
    setup['order'].tracker = tr; setup['order'].save()
    r = tc.patch(f'/api/logistics/shipments/{setup["logistics"].id}/',
                 {'tracking_no': 'PATCHED'}, format='json')
    assert r.status_code == 200
    assert r.data['data']['tracking_no'] == 'PATCHED'

def test_tracker_cannot_create_for_other_order(db):
    """tracker 给非自己订单创建物流 → 403"""
    tr = _make_user('tr_x', 'tracker')
    c = Customer.objects.create(name='C_X')
    o = Order.objects.create(order_no='O_OTHER', tracking_status='排产', customer=c)  # 无 tracker
    LogisticsProvider.objects.create(name='测试', type='domestic')
    client = APIClient(); client.force_authenticate(tr)
    r = client.post('/api/logistics/shipments/', {'order': o.id, 'tracking_no': 'X'}, format='json')
    assert r.status_code == 403

# ---- BUG-SIM-001: bulk-delete 权限必须等价于单条删除 ----

def test_tracker_cannot_bulk_delete_shipments(db, setup, tracker_client):
    tc, _ = tracker_client
    r = tc.post('/api/logistics/shipments/bulk-delete/', {'ids': [setup['logistics'].id]}, format='json')
    assert r.status_code == 403
    assert Logistics.objects.filter(id=setup['logistics'].id).exists()

def test_admin_can_bulk_delete_shipments(db, setup, admin_client):
    r = admin_client.post('/api/logistics/shipments/bulk-delete/', {'ids': [setup['logistics'].id]}, format='json')
    assert r.status_code == 200 and r.data['data']['deleted'] == 1
    assert not Logistics.objects.filter(id=setup['logistics'].id).exists()


# ---- Logistics 打回泛化（BUG-SIM-024 同规则，锁加固同口径）----

def test_tracker_edit_approved_shipment_recoils(db, setup, tracker_client):
    """tracker 编辑已批准发货单 → 打回未批准 + 重挂 logistics 审批"""
    from apps.system_mgmt.models import ApprovalRequest
    tc, tr = tracker_client
    setup['order'].tracker = tr; setup['order'].save()
    r = tc.patch(f'/api/logistics/shipments/{setup["logistics"].id}/', {'tracking_no': 'NEW2'}, format='json')
    assert r.status_code == 200
    logi = Logistics.objects.get(pk=setup['logistics'].id)
    assert logi.is_approved is False
    assert ApprovalRequest.objects.filter(
        approval_type='logistics', target_model='Logistics',
        target_id=logi.id, status='pending').exists()

def test_admin_edit_approved_shipment_no_recoil(db, setup, admin_client):
    """admin 编辑已批准发货单不打回（admin 即审批人）"""
    from apps.system_mgmt.models import ApprovalRequest
    r = admin_client.patch(f'/api/logistics/shipments/{setup["logistics"].id}/', {'tracking_no': 'NEW3'}, format='json')
    assert r.status_code == 200
    logi = Logistics.objects.get(pk=setup['logistics'].id)
    assert logi.is_approved is True
    assert not ApprovalRequest.objects.filter(target_model='Logistics', target_id=logi.id).exists()


@pytest.mark.django_db(transaction=True)
def test_recoiled_shipment_excluded_from_ledger(db):
    """审查收口：打回后收支流水物流费用源不含该发货单，approve 后恢复（跨模块联动锁）。

    调 approve 端点触发 SQLite 在线备份 → 必须 transaction=True（备份在未提交
    事务下无限等待，错题集既有条目）；实体用 reco_ 前缀唯一名——transaction=True
    的数据真实提交进共享内存库，通用名会与后跑文件的实体撞唯一键。
    """
    from apps.system_mgmt.models import ApprovalRequest
    from rest_framework.test import APIClient

    adm = User.objects.create_user('reco_admin', password='pw123456')
    adm.groups.add(Group.objects.get(name='admin'))
    tr = User.objects.create_user('reco_tracker', password='pw123456')
    tr.groups.add(Group.objects.get(name='tracker'))
    admin_c = APIClient(); admin_c.force_authenticate(adm)
    tracker_c = APIClient(); tracker_c.force_authenticate(tr)

    carrier = LogisticsProvider.objects.create(name='回款联动承运', type='domestic')
    o = Order.objects.create(
        order_no='ORECL', customer=Customer.objects.create(name='回款联动客户'), amount_usd='100')
    logi = Logistics.objects.create(order=o, domestic_carrier=carrier, tracking_no='RECO1', cost='50.00')
    o.tracker = tr; o.save()

    def _logi_rows():
        r = admin_c.get('/api/finance/payments-in/ledger/')
        return [row for row in r.data['data']['results'] if row['type'] == 'expense_logistics']

    assert len(_logi_rows()) == 1  # 前置：已批准发货单费用在流水
    r = tracker_c.patch(f'/api/logistics/shipments/{logi.id}/', {'tracking_no': 'RECO2'}, format='json')
    assert r.status_code == 200
    assert _logi_rows() == []  # 打回后流水排除
    ar = ApprovalRequest.objects.get(target_model='Logistics', target_id=logi.id, status='pending')
    r = admin_c.post(f'/api/system-mgmt/approvals/{ar.id}/approve/', format='json')
    assert r.status_code == 200
    assert len(_logi_rows()) == 1  # 批准后恢复
