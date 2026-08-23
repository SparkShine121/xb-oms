import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from apps.system_mgmt.models import ApprovalRequest, BackupRecord
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord
from apps.logistics.models import Logistics
from apps.orders.models import Order
from apps.basic_info.models import Factory, Customer


def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u


def _client(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


@pytest.fixture
def setup(db, tmp_path, settings):
    """基础数据 + 备份目录指向 tmp_path（测试不污染真实 backups/）。"""
    settings.BACKUP_DIR = str(tmp_path / 'backups')
    f = Factory.objects.create(name='华鑫')
    s1 = _make_user('sales_a', 'salesman')
    ca = Customer.objects.create(name='客户甲', salesman=s1)
    o = Order.objects.create(order_no='OA', tracking_status='排产', customer=ca,
                             salesman=s1, amount_usd='100')
    from apps.orders.models import OrderItem
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10,
                                    unit_price='10', subtotal='100', cost_price='7.20')
    return {'factory': f, 'sales': s1, 'customer': ca, 'order': o, 'item': item}


# ---- 新建挂起审批 ----

def test_finance_create_factory_payment_pends(db, setup):
    """finance（非 admin）新建结算单 → is_approved=False + 生成 settlement 审批。"""
    c = _client(_make_user('fin', 'finance'))
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00',
    }, format='json')
    assert r.status_code == 201
    fp = FactoryPayment.objects.get(pk=r.data['data']['id'])
    assert fp.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=fp.id, approval_type='settlement')
    assert ar.status == 'pending'
    assert ar.target_model == 'FactoryPayment'
    assert ar.submitted_by.username == 'fin'


def test_admin_create_factory_payment_auto_approved(db, setup):
    c = _client(_make_user('adm2', 'admin'))
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00',
    }, format='json')
    assert r.status_code == 201
    fp = FactoryPayment.objects.get(pk=r.data['data']['id'])
    assert fp.is_approved is True
    assert ApprovalRequest.objects.count() == 0


def test_finance_create_record_pends(db, setup):
    """付款记录（payment 类型）审批流。"""
    fp = FactoryPayment.objects.create(order_item=setup['item'],
                                       factory=setup['factory'], amount_cny='72.00')
    c = _client(_make_user('fin_r', 'finance'))
    r = c.post('/api/factory-payment/records/', {
        'factory_payment': fp.id, 'amount': '30.00', 'payment_date': '2026-08-23',
    }, format='json')
    assert r.status_code == 201
    rec = FactoryPaymentRecord.objects.get(pk=r.data['data']['id'])
    assert rec.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=rec.id, approval_type='payment')
    assert ar.target_model == 'FactoryPaymentRecord'
    assert ar.status == 'pending'


def test_tracker_create_logistics_pends(db, setup):
    """tracker 为派给自己的订单登记物流 → 挂审批。"""
    t = _make_user('trk_l', 'tracker')
    setup['order'].tracker = t
    setup['order'].save()
    c = _client(t)
    r = c.post('/api/logistics/shipments/', {'order': setup['order'].id}, format='json')
    assert r.status_code == 201
    lg = Logistics.objects.get(pk=r.data['data']['id'])
    assert lg.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=lg.id, approval_type='logistics')
    assert ar.target_model == 'Logistics'


def test_salesman_create_order_pends(db, setup):
    """业务员新建订单 → order_change 审批；admin 新建直接通过。"""
    c = _client(setup['sales'])
    r = c.post('/api/orders/orders/', {
        'order_no': 'OB-NEW', 'amount_usd': '50.00', 'items': [],
    }, format='json')
    assert r.status_code == 201, r.data
    od = Order.objects.get(order_no='OB-NEW')
    assert od.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=od.id, approval_type='order_change')
    assert ar.target_model == 'Order'

    adm = _client(_make_user('adm_o', 'admin'))
    r = adm.post('/api/orders/orders/', {'order_no': 'OC-NEW', 'items': []}, format='json')
    assert r.status_code == 201
    od2 = Order.objects.get(order_no='OC-NEW')
    assert od2.is_approved is True


# ---- approve / reject ----

# 注意：sqlite3 .backup() 在 pytest-django 默认的事务包裹下会死锁
# （共享缓存内存库 + 未提交写事务），备份相关用例须用 transaction=True 贴近生产的 autocommit。

@pytest.mark.django_db(transaction=True)
def test_admin_approve_flips_target_and_backs_up(setup):
    fin = _make_user('fin_ap', 'finance')
    c = _client(fin)
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00',
    }, format='json')
    fp_id = r.data['data']['id']
    ar = ApprovalRequest.objects.get(target_id=fp_id)

    adm = _client(_make_user('adm_ap', 'admin'))
    r = adm.post(f'/api/system-mgmt/approvals/{ar.id}/approve/', format='json')
    assert r.status_code == 200

    fp = FactoryPayment.objects.get(pk=fp_id)
    assert fp.is_approved is True
    ar.refresh_from_db()
    assert ar.status == 'approved'
    assert ar.reviewed_by.username == 'adm_ap'

    # 审批通过自动备份：生成 BackupRecord(trigger=approval) + 落盘文件
    brs = BackupRecord.objects.filter(trigger='approval')
    assert brs.count() == 1
    import os
    assert os.path.exists(brs.first().file_path)


def test_admin_reject_sets_status(db, setup):
    c = _client(_make_user('fin_rj', 'finance'))
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '9999.00',
    }, format='json')
    fp_id = r.data['data']['id']
    ar = ApprovalRequest.objects.get(target_id=fp_id)

    adm = _client(_make_user('adm_rj', 'admin'))
    r = adm.post(f'/api/system-mgmt/approvals/{ar.id}/reject/',
                 {'note': '金额有误'}, format='json')
    assert r.status_code == 200
    ar.refresh_from_db()
    assert ar.status == 'rejected'
    # 驳回不改 target，is_approved 保持 False，可改后重提
    assert FactoryPayment.objects.get(pk=fp_id).is_approved is False


def test_non_admin_cannot_list_or_review(db, setup):
    fin = _client(_make_user('fin_na', 'finance'))
    assert fin.get('/api/system-mgmt/approvals/').status_code == 403
    ar = ApprovalRequest.objects.create(
        approval_type='settlement', target_id=1, target_model='FactoryPayment')
    assert fin.post(f'/api/system-mgmt/approvals/{ar.id}/approve/').status_code == 403
    assert fin.post(f'/api/system-mgmt/approvals/{ar.id}/reject/').status_code == 403


# ---- serializer 暴露 is_approved（审查修复 #2）----

def test_serializer_exposes_is_approved_and_client_cannot_set(db, setup):
    """is_approved 只读暴露：客户端伪造 true 被忽略，仍按审批流置 False。"""
    c = _client(_make_user('fin_ser', 'finance'))
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00', 'is_approved': True,
    }, format='json')
    assert r.status_code == 201
    assert r.data['data']['is_approved'] is False


# ---- 驳回后重提（审查修复 #3）----

def test_rejected_factory_payment_can_be_resubmitted(db, setup):
    fin = _make_user('fin_rs', 'finance')
    c = _client(fin)
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00'}, format='json')
    fp_id = r.data['data']['id']
    ar = ApprovalRequest.objects.get(target_id=fp_id, approval_type='settlement')

    adm = _client(_make_user('adm_rs', 'admin'))
    adm.post(f'/api/system-mgmt/approvals/{ar.id}/reject/', {'note': '金额有误'}, format='json')

    # 非 admin 修改被驳回的记录 → 重置待审批 + 生成新申请
    r = c.patch(f'/api/factory-payment/payments/{fp_id}/', {'amount_cny': '80.00'}, format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.get(pk=fp_id).is_approved is False
    ar.refresh_from_db()
    assert ar.status == 'rejected'  # 旧申请保持驳回留痕
    new_ar = (ApprovalRequest.objects.filter(target_id=fp_id, approval_type='settlement')
              .order_by('-id').first())
    assert new_ar.id != ar.id
    assert new_ar.status == 'pending'


def test_rejected_order_can_be_resubmitted(db, setup):
    s1 = setup['sales']
    c = _client(s1)
    # 带 customer（salesman 的数据范围按 customer__salesman 过滤，须落在自己范围内）
    r = c.post('/api/orders/orders/', {'order_no': 'OB-RESUB', 'customer': setup['customer'].id,
                                       'items': []}, format='json')
    od_id = r.data['data']['id']
    ar = ApprovalRequest.objects.get(target_id=od_id, approval_type='order_change')

    adm = _client(_make_user('adm_orj', 'admin'))
    adm.post(f'/api/system-mgmt/approvals/{ar.id}/reject/', format='json')

    r = c.patch(f'/api/orders/orders/{od_id}/', {'amount_usd': '60.00'}, format='json')
    assert r.status_code == 200
    new_ar = (ApprovalRequest.objects.filter(target_id=od_id, approval_type='order_change')
              .order_by('-id').first())
    assert new_ar.id != ar.id and new_ar.status == 'pending'


def test_update_pending_does_not_duplicate_request(db, setup):
    """待审中编辑：不重复创建申请。"""
    c = _client(_make_user('fin_dup', 'finance'))
    r = c.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00'}, format='json')
    fp_id = r.data['data']['id']
    count_before = ApprovalRequest.objects.count()
    r = c.patch(f'/api/factory-payment/payments/{fp_id}/', {'note': '改备注'}, format='json')
    assert r.status_code == 200
    assert ApprovalRequest.objects.count() == count_before


def test_admin_edit_does_not_create_request(db, setup):
    """admin 编辑已批准数据不产生新申请。"""
    adm = _client(_make_user('adm_ed', 'admin'))
    r = adm.post('/api/factory-payment/payments/', {
        'order_item': setup['item'].id, 'factory': setup['factory'].id,
        'amount_cny': '72.00'}, format='json')
    assert r.status_code == 201
    fp_id = r.data['data']['id']
    assert ApprovalRequest.objects.count() == 0
    r = adm.patch(f'/api/factory-payment/payments/{fp_id}/', {'note': 'x'}, format='json')
    assert r.status_code == 200
    assert ApprovalRequest.objects.count() == 0


# ---- 批量写入路径审批流（final review 修复）----

def test_import_data_pends_for_salesman(db, setup):
    """Excel 导入审批流：salesman 导入的新建订单挂起待审批；admin 导入直接生效。"""
    from io import BytesIO
    import openpyxl

    def make_xlsx(order_no):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['订单名称', '联系人'])  # 其余列缺省走导入器默认值
        ws.append([order_no, '客户甲'])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    c = _client(setup['sales'])
    r = c.post('/api/orders/orders/import/', {'file': make_xlsx('OIMP-1')}, format='multipart')
    assert r.status_code == 200, r.data
    assert r.data['data']['created_order_nos'] == ['OIMP-1']
    od = Order.objects.get(order_no='OIMP-1')
    assert od.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=od.id, approval_type='order_change')
    assert ar.target_model == 'Order'
    assert ar.status == 'pending'
    assert ar.submitted_by.username == 'sales_a'

    adm = _client(_make_user('adm_imp', 'admin'))
    r = adm.post('/api/orders/orders/import/', {'file': make_xlsx('OIMP-2')}, format='multipart')
    assert r.status_code == 200
    assert Order.objects.get(order_no='OIMP-2').is_approved is True
    assert not ApprovalRequest.objects.filter(
        target_id=Order.objects.get(order_no='OIMP-2').id).exists()


def test_generate_by_order_pends_for_non_admin(db, setup):
    """一键生成结算单审批流：finance 生成 → 挂起；admin 生成 → 直接生效。"""
    fin = _client(_make_user('fin_gen', 'finance'))
    r = fin.post(f"/api/factory-payment/payments/orders/{setup['order'].id}/generate/",
                 format='json')
    assert r.status_code == 200
    fp = FactoryPayment.objects.get(order_item=setup['item'])
    assert fp.is_approved is False
    ar = ApprovalRequest.objects.get(target_id=fp.id, approval_type='settlement')
    assert ar.status == 'pending'
    assert ar.target_model == 'FactoryPayment'
    assert ar.submitted_by.username == 'fin_gen'

    # 新增一个带工厂的 item，admin 再生成 → 该 item 的结算单直接生效
    from apps.orders.models import OrderItem
    f2 = Factory.objects.create(name='华鑫二号')
    item2 = OrderItem.objects.create(order=setup['order'], seq=2, factory=f2, qty=5,
                                     unit_price='10', subtotal='50', cost_price='7.20')
    adm = _client(_make_user('adm_gen', 'admin'))
    r = adm.post(f"/api/factory-payment/payments/orders/{setup['order'].id}/generate/",
                 format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.get(order_item=item2).is_approved is True


# ---- 备份 ----

@pytest.mark.django_db(transaction=True)
def test_manual_backup_and_download(setup):
    adm = _client(_make_user('adm_bk', 'admin'))
    r = adm.post('/api/system-mgmt/backups/manual-backup/', format='json')
    assert r.status_code in (200, 201)
    brs = list(BackupRecord.objects.filter(trigger='manual'))
    assert len(brs) == 1
    import os
    assert os.path.exists(brs[0].file_path) and os.path.getsize(brs[0].file_path) > 0

    r = adm.get(f"/api/system-mgmt/backups/{brs[0].id}/download/")
    assert r.status_code == 200
    assert b'SQLite' in b''.join(r.streaming_content)


@pytest.mark.django_db(transaction=True)
def test_backup_rolling_cleanup(setup, settings):
    """超过保留上限删最旧（DB 记录 + 文件）。"""
    settings.BACKUP_MAX_COUNT = 3
    adm = _client(_make_user('adm_rc', 'admin'))
    for _ in range(5):
        adm.post('/api/system-mgmt/backups/manual-backup/', format='json')
    assert BackupRecord.objects.count() == 3
    import os
    for br in BackupRecord.objects.all():
        assert os.path.exists(br.file_path)


def test_operation_log_list_admin_only(db, setup):
    from apps.system_mgmt.models import OperationLog
    u = _make_user('op_u', 'admin')
    OperationLog.objects.create(user=u, action='POST', path='/api/orders/orders/')
    OperationLog.objects.create(user=u, action='DELETE', path='/api/basic-info/factories/')

    adm = _client(u)
    r = adm.get('/api/system-mgmt/logs/')
    assert r.status_code == 200
    assert r.data['data']['count'] == 2
    # 筛选
    r = adm.get('/api/system-mgmt/logs/', {'action': 'DELETE'})
    assert r.data['data']['count'] == 1

    non_admin = _client(setup['sales'])
    assert non_admin.get('/api/system-mgmt/logs/').status_code == 403
