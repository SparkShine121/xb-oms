import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order
from io import BytesIO

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_create_order(admin_client, db):
    r = admin_client.post('/api/orders/orders/', {'order_no':'O1','amount_usd':'100','items':[]}, format='json')
    assert r.status_code == 201 and r.data['data']['order_no'] == 'O1'

def test_import_action_bad_file(admin_client, db):
    f = BytesIO(b'not xlsx'); f.name = 'bad.xlsx'
    r = admin_client.post('/api/orders/orders/import/', {'file': f}, format='multipart')
    assert r.status_code == 400  # 坏文件容错

def test_import_template_download(admin_client, db):
    r = admin_client.get('/api/orders/orders/import-template/')
    assert r.status_code == 200

def test_exchange_rate_crud_admin(admin_client, db):
    r = admin_client.post('/api/orders/exchange-rates/', {'currency_pair':'USD/CNY','rate':'7.20','effective_date':'2026-08-01'}, format='json')
    assert r.status_code == 201
    r2 = admin_client.get('/api/orders/exchange-rates/')
    assert r2.status_code == 200

def test_exchange_rate_non_admin_forbidden(db):
    from django.contrib.auth.models import User, Group
    u = User.objects.create_user('sales1', password='pw123456'); u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u)
    r = c.post('/api/orders/exchange-rates/', {'currency_pair':'USD/CNY','rate':'7.20','effective_date':'2026-08-01'}, format='json')
    assert r.status_code == 403
def test_salesman_cannot_change_salesman_on_update(db):
    """非 admin 更新订单时,派单字段(salesman/tracker)应被忽略——仅 admin 可改"""
    from apps.basic_info.models import Customer
    admin = User.objects.create_user('admin2', password='pw123456')
    admin.groups.add(Group.objects.get(name='admin'))
    sales1 = User.objects.create_user('salesA', password='pw123456')
    sales1.groups.add(Group.objects.get(name='salesman'))
    sales2 = User.objects.create_user('salesB', password='pw123456')
    sales2.groups.add(Group.objects.get(name='salesman'))
    cust = Customer.objects.create(name='客户甲', salesman=sales1)
    order = Order.objects.create(order_no='OO1', customer=cust, salesman=sales1)
    client = APIClient(); client.force_authenticate(sales1)
    r = client.patch(f'/api/orders/orders/{order.id}/',
                     {'remark': '业务员改备注', 'salesman': sales2.id}, format='json')
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.salesman_id == sales1.id      # salesman 变更被忽略
    assert order.remark == '业务员改备注'        # 其他字段正常更新
    # admin 可以改
    cadmin = APIClient(); cadmin.force_authenticate(admin)
    r2 = cadmin.patch(f'/api/orders/orders/{order.id}/', {'salesman': sales2.id}, format='json')
    assert r2.status_code == 200
    order.refresh_from_db()
    assert order.salesman_id == sales2.id      # admin 修改生效

# ---- BUG-SIM-002: 挂结算订单删除保护（Q5:i）----
from apps.basic_info.models import Customer
from apps.basic_info.models import Factory as OrderFactory
from apps.orders.models import OrderItem
from apps.factory_payment.models import FactoryPayment


def _make_orders_with_settlement():
    f = OrderFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='C1')
    o_settled = Order.objects.create(order_no='OS', customer=c)
    item = OrderItem.objects.create(order=o_settled, seq=1, product_no='P1', qty=1, subtotal='100', cost_price='72')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    o_plain = Order.objects.create(order_no='OP', customer=c)
    OrderItem.objects.create(order=o_plain, seq=1, product_no='P9', qty=1, subtotal='50', cost_price='36')
    return o_settled, o_plain


def test_destroy_order_with_settlement_rejected(db, admin_client):
    o_settled, _ = _make_orders_with_settlement()
    r = admin_client.delete(f'/api/orders/orders/{o_settled.id}/')
    assert r.status_code == 400
    assert Order.objects.filter(id=o_settled.id).exists()
    assert FactoryPayment.objects.count() == 1


def test_destroy_order_without_settlement_ok(db, admin_client):
    _, o_plain = _make_orders_with_settlement()
    r = admin_client.delete(f'/api/orders/orders/{o_plain.id}/')
    assert r.status_code == 200
    assert not Order.objects.filter(id=o_plain.id).exists()


def test_bulk_delete_mixed_settlement_reports_forbidden(db, admin_client):
    o_settled, o_plain = _make_orders_with_settlement()
    r = admin_client.post('/api/orders/orders/bulk-delete/', {'ids': [o_settled.id, o_plain.id]}, format='json')
    assert r.status_code == 200
    assert r.data['data']['deleted'] == 1
    assert r.data['data']['forbidden'] == [o_settled.id]
    assert Order.objects.filter(id=o_settled.id).exists()
    assert FactoryPayment.objects.count() == 1

# ---- BUG-SIM-012: 汇率 rate>0 校验 ----

def test_exchange_rate_non_positive_rejected(db, admin_client):
    for bad in ('0', '-7.2'):
        r = admin_client.post('/api/orders/exchange-rates/',
                              {'currency_pair': 'USD/CNY', 'rate': bad, 'effective_date': '2026-09-17'}, format='json')
        assert r.status_code == 400, bad

# ---- BUG-SIM-007: 汇率 (币种对, 日期) 唯一 ----

def test_duplicate_exchange_rate_rejected(db, admin_client):
    r1 = admin_client.post('/api/orders/exchange-rates/',
                           {'currency_pair': 'USD/CNY', 'rate': '7.2', 'effective_date': '2026-09-01'}, format='json')
    assert r1.status_code == 201
    r2 = admin_client.post('/api/orders/exchange-rates/',
                           {'currency_pair': 'USD/CNY', 'rate': '7.5', 'effective_date': '2026-09-01'}, format='json')
    assert r2.status_code == 400

def test_same_pair_different_date_allowed(db, admin_client):
    r = admin_client.post('/api/orders/exchange-rates/',
                          {'currency_pair': 'USD/CNY', 'rate': '7.5', 'effective_date': '2026-10-01'}, format='json')
    assert r.status_code == 201

def test_same_date_different_pair_allowed(db, admin_client):
    r = admin_client.post('/api/orders/exchange-rates/',
                          {'currency_pair': 'EUR/CNY', 'rate': '7.9', 'effective_date': '2026-09-01'}, format='json')
    assert r.status_code == 201

# ---- BUG-SIM-007 followup：PATCH 场景回归锁 ----

def test_exchange_rate_patch_date_to_occupied_rejected(db, admin_client):
    """PATCH 汇率生效日期到同币种对已占日期 → 400"""
    admin_client.post('/api/orders/exchange-rates/',
                      {'currency_pair': 'USD/CNY', 'rate': '7.2', 'effective_date': '2026-09-01'}, format='json')
    r2 = admin_client.post('/api/orders/exchange-rates/',
                           {'currency_pair': 'USD/CNY', 'rate': '7.5', 'effective_date': '2026-10-01'}, format='json')
    rid = r2.data['data']['id']
    r3 = admin_client.patch(f'/api/orders/exchange-rates/{rid}/', {'effective_date': '2026-09-01'}, format='json')
    assert r3.status_code == 400

# ---- BUG-SIM-016: 重复 order_no 定制文案 ----

def test_duplicate_order_no_friendly_message(db, admin_client):
    r1 = admin_client.post('/api/orders/orders/', {'order_no': 'ODUP', 'amount_usd': '1', 'items': []}, format='json')
    assert r1.status_code == 201
    r2 = admin_client.post('/api/orders/orders/', {'order_no': 'ODUP', 'amount_usd': '1', 'items': []}, format='json')
    assert r2.status_code == 400
    assert 'ODUP 已存在' in str(r2.data['message'])

# ---- BUG-SIM-004/014: 建单归属 + set-tracker 校验 ----
from apps.tracking.models import TrackingLog as _TL  # noqa
from apps.system_mgmt.models import ApprovalRequest


def _sales_user(name='sales_own'):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    return u


def test_salesman_create_forces_self_ownership(db):
    """非 admin 建单：payload 指定 salesman=别人/tracker=财务 全部被忽略"""
    from apps.basic_info.models import Customer
    sales = _sales_user()
    other = _sales_user('sales_other')
    fin = User.objects.create_user('fin_x', password='pw123456'); fin.groups.add(Group.objects.get(name='finance'))
    cust = Customer.objects.create(name='自己的客户', salesman=sales)
    c = APIClient(); c.force_authenticate(sales)
    r = c.post('/api/orders/orders/', {
        'order_no': 'OOWN', 'amount_usd': '100', 'customer': cust.id,
        'salesman': other.id, 'tracker': fin.id, 'items': [],
    }, format='json')
    assert r.status_code == 201
    o = Order.objects.get(order_no='OOWN')
    assert o.salesman_id == sales.id      # 强制=建单人（payload 被忽略）
    assert o.tracker_id is None           # tracker 忽略置空待派单


def test_salesman_create_other_customer_rejected(db):
    """非 admin 建单只能选自己客户"""
    from apps.basic_info.models import Customer
    sales = _sales_user('sales_a2')
    other_sales = _sales_user('sales_b2')
    other_cust = Customer.objects.create(name='别人的客户', salesman=other_sales)
    c = APIClient(); c.force_authenticate(sales)
    r = c.post('/api/orders/orders/', {
        'order_no': 'OOTH', 'amount_usd': '100', 'customer': other_cust.id, 'items': [],
    }, format='json')
    assert r.status_code == 400


def test_salesman_create_own_customer_still_works(db):
    """回归锁：建自己客户正常 + 挂审批"""
    from apps.basic_info.models import Customer
    sales = _sales_user('sales_ok')
    cust = Customer.objects.create(name='我的客户', salesman=sales)
    c = APIClient(); c.force_authenticate(sales)
    before = ApprovalRequest.objects.count()
    r = c.post('/api/orders/orders/', {
        'order_no': 'OOMY', 'amount_usd': '100', 'customer': cust.id, 'items': [],
    }, format='json')
    assert r.status_code == 201
    assert ApprovalRequest.objects.count() == before + 1  # 非 admin 建单挂审批
    o = Order.objects.get(order_no='OOMY')
    assert o.is_approved is False


def test_salesman_import_forbidden(db):
    """导入收紧为仅 admin（Q1'）"""
    sales = _sales_user('sales_imp')
    c = APIClient(); c.force_authenticate(sales)
    from io import BytesIO
    f = BytesIO(b'not xlsx'); f.name = 'x.xlsx'
    r = c.post('/api/orders/orders/import/', {'file': f}, format='multipart')
    assert r.status_code == 403


def test_finance_set_tracker_forbidden(db):
    """set-tracker 收紧为仅 admin（Q2:a）——finance 绕前端直调 → 403"""
    from apps.basic_info.models import Customer
    fin = User.objects.create_user('fin_st', password='pw123456'); fin.groups.add(Group.objects.get(name='finance'))
    tr = User.objects.create_user('tr_st', password='pw123456'); tr.groups.add(Group.objects.get(name='tracker'))
    o = Order.objects.create(order_no='OST1', customer=Customer.objects.create(name='C'))
    c = APIClient(); c.force_authenticate(fin)
    r = c.post(f'/api/orders/orders/{o.id}/set-tracker/', {'tracker': tr.id}, format='json')
    assert r.status_code == 403


def test_admin_set_tracker_non_tracker_role_rejected(db):
    """admin 派单目标必须 tracker 角色（Q3:a）"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_st', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    sales = _sales_user('sales_st')
    o = Order.objects.create(order_no='OST2', customer=Customer.objects.create(name='C2'))
    c = APIClient(); c.force_authenticate(adm)
    r = c.post(f'/api/orders/orders/{o.id}/set-tracker/', {'tracker': sales.id}, format='json')
    assert r.status_code == 400
    o.refresh_from_db()
    assert o.tracker_id is None


def test_admin_set_tracker_tracker_role_ok(db):
    """回归锁：admin 派给 tracker 角色成功"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_st2', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    tr = User.objects.create_user('tr_st2', password='pw123456'); tr.groups.add(Group.objects.get(name='tracker'))
    o = Order.objects.create(order_no='OST3', customer=Customer.objects.create(name='C3'))
    c = APIClient(); c.force_authenticate(adm)
    r = c.post(f'/api/orders/orders/{o.id}/set-tracker/', {'tracker': tr.id}, format='json')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracker_id == tr.id


def test_admin_create_can_assign_roles(db):
    """回归锁：admin 建单可任意指定 salesman/tracker（但 tracker 须为 tracker 角色）"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_cr', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    sales = _sales_user('sales_cr')
    tr = User.objects.create_user('tr_cr', password='pw123456'); tr.groups.add(Group.objects.get(name='tracker'))
    cust = Customer.objects.create(name='C4', salesman=sales)
    c = APIClient(); c.force_authenticate(adm)
    r = c.post('/api/orders/orders/', {
        'order_no': 'OADM', 'amount_usd': '100', 'customer': cust.id,
        'salesman': sales.id, 'tracker': tr.id, 'items': [],
    }, format='json')
    assert r.status_code == 201
    o = Order.objects.get(order_no='OADM')
    assert (o.salesman_id, o.tracker_id) == (sales.id, tr.id)


def test_admin_create_tracker_non_role_rejected(db):
    """Q3:a：admin 建单指定非 tracker 角色的 tracker → 400"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_cr2', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    sales = _sales_user('sales_cr2')
    cust = Customer.objects.create(name='C5', salesman=sales)
    c = APIClient(); c.force_authenticate(adm)
    r = c.post('/api/orders/orders/', {
        'order_no': 'OADM2', 'amount_usd': '100', 'customer': cust.id,
        'tracker': sales.id, 'items': [],
    }, format='json')
    assert r.status_code == 400

# ---- BUG-SIM-004/014 followup（旁观者审查发现）----

def test_patch_order_with_legacy_orphan_tracker_allowed(db):
    """遗留数据兼容：订单挂着非 tracker 角色的历史 tracker，admin 原值编辑不误伤"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_leg', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    fin = User.objects.create_user('fin_leg', password='pw123456'); fin.groups.add(Group.objects.get(name='finance'))
    o = Order.objects.create(order_no='OLEG', customer=Customer.objects.create(name='C'), tracker=fin)  # 历史孤儿数据
    c = APIClient(); c.force_authenticate(adm)
    r = c.patch(f'/api/orders/orders/{o.id}/', {'remark': '改备注', 'tracker': fin.id}, format='json')
    assert r.status_code == 200  # 未改动的原值豁免
    r2 = c.patch(f'/api/orders/orders/{o.id}/', {'tracker': fin.id}, format='json')  # 改成另一个非 tracker 也不行
    assert r2.status_code == 200  # 仍是原值
    sales = User.objects.create_user('sales_leg', password='pw123456'); sales.groups.add(Group.objects.get(name='salesman'))
    r3 = c.patch(f'/api/orders/orders/{o.id}/', {'tracker': sales.id}, format='json')
    assert r3.status_code == 400  # 换成非 tracker 角色 → 拒绝


def test_finance_import_forbidden(db):
    """Q1'：导入仅 admin，finance → 403"""
    fin = User.objects.create_user('fin_imp', password='pw123456'); fin.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(fin)
    from io import BytesIO
    f = BytesIO(b'not xlsx'); f.name = 'x.xlsx'
    r = c.post('/api/orders/orders/import/', {'file': f}, format='multipart')
    assert r.status_code == 403

def test_salesman_create_without_customer_rejected(db):
    """非 admin 建单必须选客户（否则产生建单人自己都看不见的悬空单）"""
    sales = _sales_user('sales_nocust')
    c = APIClient(); c.force_authenticate(sales)
    r = c.post('/api/orders/orders/', {'order_no': 'ONC', 'amount_usd': '1', 'items': []}, format='json')
    assert r.status_code == 400

# ---- BUG-SIM-013: 编辑页状态处理 ----

def test_salesman_edit_tracking_status_ignored(db):
    """非 admin 编辑时 tracking_status 被忽略（状态机唯一入口=跟单流转）"""
    from apps.basic_info.models import Customer
    sales = _sales_user('sales_ts')
    o = Order.objects.create(order_no='OTS1', tracking_status='排产',
                             customer=Customer.objects.create(name='C', salesman=sales), salesman=sales)
    c = APIClient(); c.force_authenticate(sales)
    r = c.patch(f'/api/orders/orders/{o.id}/', {'tracking_status': '发货', 'remark': '改备注'}, format='json')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracking_status == '排产'  # 未被跳节点
    assert o.remark == '改备注'  # 其余字段照常


def test_admin_edit_to_cancelled_rejected(db):
    """admin 编辑也不能置"已取消"——取消必须走显式 is_cancelled 操作"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_ts', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    o = Order.objects.create(order_no='OTS2', tracking_status='排产', customer=Customer.objects.create(name='C2'))
    c = APIClient(); c.force_authenticate(adm)
    r = c.patch(f'/api/orders/orders/{o.id}/', {'tracking_status': '已取消'}, format='json')
    assert r.status_code == 400
    o.refresh_from_db()
    assert o.tracking_status == '排产' and o.is_cancelled is False


def test_admin_edit_status_correction_ok(db):
    """回归锁：admin 纠错改其他状态正常"""
    from apps.basic_info.models import Customer
    adm = User.objects.create_user('adm_ts2', password='pw123456'); adm.groups.add(Group.objects.get(name='admin'))
    o = Order.objects.create(order_no='OTS3', tracking_status='排产', customer=Customer.objects.create(name='C3'))
    c = APIClient(); c.force_authenticate(adm)
    r = c.patch(f'/api/orders/orders/{o.id}/', {'tracking_status': '生产中'}, format='json')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracking_status == '生产中'
