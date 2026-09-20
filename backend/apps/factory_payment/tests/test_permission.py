import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory, Customer
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def finance_client(db):
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u); return c

@pytest.fixture
def salesman_client(db):
    u = User.objects.create_user('sales1', password='pw123456')
    u.groups.add(Group.objects.get(name='salesman'))
    c = APIClient(); c.force_authenticate(u); return c

def test_admin_can_create(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = admin_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 201

def test_finance_can_create(db, finance_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = finance_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 201

def test_salesman_cannot_create(db, salesman_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = salesman_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': f.id, 'amount_cny': '72.00'
    }, format='json')
    assert r.status_code == 403

def test_salesman_cannot_generate(db, salesman_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = salesman_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 403

def test_finance_cannot_delete(db, finance_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = finance_client.delete(f'/api/factory-payment/payments/{fp.id}/')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(pk=fp.pk).exists()

def test_record_delete_reaggregates(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    FactoryPaymentRecord.objects.create(factory_payment=fp, amount='30.00', payment_date='2026-08-14')
    rec2 = FactoryPaymentRecord.objects.create(factory_payment=fp, amount='42.00', payment_date='2026-08-15')
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '72.00'
    assert fp.status == '已结'
    r = admin_client.delete(f'/api/factory-payment/records/{rec2.id}/')
    assert r.status_code == 200
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '30.00'
    assert fp.status == '部分结'

# ---- BUG-SIM-001: bulk-delete 权限必须等价于单条删除 ----

def _make_payment():
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    return FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')

def test_finance_cannot_bulk_delete_payments(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(id=p.id).exists()

def test_salesman_cannot_bulk_delete_payments(db, salesman_client):
    p = _make_payment()
    r = salesman_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 403
    assert FactoryPayment.objects.filter(id=p.id).exists()

def test_admin_can_bulk_delete_payments(db, admin_client):
    p = _make_payment()
    r = admin_client.post('/api/factory-payment/payments/bulk-delete/', {'ids': [p.id]}, format='json')
    assert r.status_code == 200 and r.data['data']['deleted'] == 1
    assert not FactoryPayment.objects.filter(id=p.id).exists()

# ---- BUG-SIM-006/012: 金额校验 ----

def test_negative_payment_record_rejected(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '-100', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 400
    p.refresh_from_db()
    assert str(p.paid_amount) == '0.00' and p.status == '未结'

def test_zero_payment_record_rejected(db, finance_client):
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '0', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 400

def test_overpay_record_rejected(db, finance_client):
    p = _make_payment()  # amount_cny=72
    r1 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '50', 'payment_date': '2026-09-17'}, format='json')
    assert r1.status_code == 201
    r2 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '30', 'payment_date': '2026-09-17'}, format='json')
    assert r2.status_code == 400  # 50+30 > 72
    p.refresh_from_db()
    assert str(p.paid_amount) == '50.00' and p.status == '部分结'

def test_pay_exact_amount_settles(db, finance_client):
    """回归锁：恰好付满正常放行并置已结"""
    p = _make_payment()
    r = finance_client.post('/api/factory-payment/records/',
                            {'factory_payment': p.id, 'amount': '72', 'payment_date': '2026-09-17'}, format='json')
    assert r.status_code == 201
    p.refresh_from_db()
    assert p.status == '已结'

def test_overpay_via_record_update_rejected(db, finance_client):
    p = _make_payment()
    r1 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '50', 'payment_date': '2026-09-17'}, format='json')
    rid = r1.data['data']['id']
    r2 = finance_client.patch(f'/api/factory-payment/records/{rid}/', {'amount': '80'}, format='json')
    assert r2.status_code == 400  # 改大后 80 > 72
    p.refresh_from_db()
    assert str(p.paid_amount) == '50.00'

def test_non_positive_settlement_amount_rejected(db, admin_client):
    from apps.basic_info.models import Factory as FPFactory
    f = FPFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='OZ', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    for bad in ('0', '-5'):
        r = admin_client.post('/api/factory-payment/payments/',
                              {'order_item': item.id, 'factory': f.id, 'amount_cny': bad}, format='json')
        assert r.status_code == 400, bad

# ---- BUG-SIM-006 followup（旁观者审查发现）----

def test_record_cannot_switch_parent_settlement(db, finance_client):
    """PATCH 付款记录不得更换所属结算单（换父会绕过超付校验并使旧父 paid_amount 失真）"""
    p = _make_payment()
    r1 = finance_client.post('/api/factory-payment/records/',
                             {'factory_payment': p.id, 'amount': '50', 'payment_date': '2026-09-17'}, format='json')
    rid = r1.data['data']['id']
    # 第二张结算单：复用同一工厂（工厂名唯一），用新订单号避免唯一冲突
    f = Factory.objects.get(name='华鑫')
    c2 = Customer.objects.create(name='客户B')
    o2 = Order.objects.create(order_no='O1b', tracking_status='排产', customer=c2, amount_usd='100')
    item2 = OrderItem.objects.create(order=o2, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    p2 = FactoryPayment.objects.create(order_item=item2, factory=f, amount_cny='72.00')
    r2 = finance_client.patch(f'/api/factory-payment/records/{rid}/',
                              {'factory_payment': p2.id}, format='json')
    assert r2.status_code == 400
    assert FactoryPaymentRecord.objects.get(id=rid).factory_payment_id == p.id

def test_settlement_amount_below_paid_rejected(db, admin_client):
    """结算单改小金额不得低于已付（否则静默"已结"并绕过超付不变量）"""
    from apps.basic_info.models import Factory as FPFactory
    f = FPFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='OS2', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = admin_client.post('/api/factory-payment/payments/',
                          {'order_item': item.id, 'factory': f.id, 'amount_cny': '100'}, format='json')
    fid = r.data['data']['id']
    admin_client.post('/api/factory-payment/records/',
                      {'factory_payment': fid, 'amount': '80', 'payment_date': '2026-09-17'}, format='json')
    r2 = admin_client.patch(f'/api/factory-payment/payments/{fid}/', {'amount_cny': '50'}, format='json')
    assert r2.status_code == 400  # 50 < 已付 80

def test_generate_skips_zero_cost_items(db, admin_client):
    """一键生成：成本为 0 的明细跳过（0 元结算单是脏数据），不整批 500"""
    from apps.basic_info.models import Factory as FPFactory
    f = FPFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='OG', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    OrderItem.objects.create(order=o, seq=2, factory=f, qty=5, unit_price='10', subtotal='50', cost_price='0')
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert r.data['data']['created_count'] == 1  # 只有正常明细生成
    assert FactoryPayment.objects.filter(order_item__order=o).count() == 1

# ---- BUG-SIM-010 回归锁（审查收口）----

def test_generate_twice_skips_all(db, admin_client):
    """同一订单重复一键生成：第二次 created=0、skipped=全部明细（锁内重查语义）"""
    from apps.basic_info.models import Factory as FPFactory
    f = FPFactory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='OG2', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    OrderItem.objects.create(order=o, seq=2, factory=f, qty=5, unit_price='10', subtotal='50', cost_price='3.60')
    r1 = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r1.status_code == 200 and r1.data['data']['created_count'] == 2
    r2 = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r2.status_code == 200
    assert r2.data['data']['created_count'] == 0 and r2.data['data']['skipped_count'] == 2

def test_shipment_seq_after_middle_delete(db):
    """回归锁：删除中间序号后仍可继续建单（max+1 取号）"""
    from apps.basic_info.models import LogisticsProvider
    from apps.logistics.models import Logistics
    carrier = LogisticsProvider.objects.create(name='顺丰', type='domestic')
    o = Order.objects.create(order_no='OL3', customer=Customer.objects.create(name='C3'))
    a = Logistics.objects.create(order=o, tracking_no='A')
    b = Logistics.objects.create(order=o, tracking_no='B')
    cc = Logistics.objects.create(order=o, tracking_no='C')
    assert (a.seq, b.seq, cc.seq) == (1, 2, 3)
    b.delete()
    d = Logistics.objects.create(order=o, tracking_no='D')
    assert d.seq == 4  # max+1，不再被 count 误导

# ---- BUG-SIM-015: 取消单财务冻结 ----

def _cancelled_order_item():
    f = Factory.objects.create(name='华鑫X')
    c = Customer.objects.create(name='客户X')
    o = Order.objects.create(order_no='OCX', tracking_status='已取消', is_cancelled=True, customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    return o, item

def test_generate_skips_cancelled_order_items(db, admin_client):
    """取消订单的明细不再参与一键生成（全 skipped）"""
    o, item = _cancelled_order_item()
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert r.data['data']['created_count'] == 0 and r.data['data']['skipped_count'] == 1
    assert FactoryPayment.objects.count() == 0

def test_manual_settlement_for_cancelled_order_rejected(db, admin_client):
    """取消订单手动新建结算 → 400"""
    o, item = _cancelled_order_item()
    r = admin_client.post('/api/factory-payment/payments/', {
        'order_item': item.id, 'factory': item.factory.id, 'amount_cny': '72'}, format='json')
    assert r.status_code == 400

def test_payment_record_on_legacy_settlement_of_cancelled_order_ok(db, finance_client):
    """回归锁：取消前已存在的结算单，付款清偿仍可登记"""
    o, item = _cancelled_order_item()
    fp = FactoryPayment.objects.create(order_item=item, factory=item.factory, amount_cny='72.00')
    r = finance_client.post('/api/factory-payment/records/', {
        'factory_payment': fp.id, 'amount': '50', 'payment_date': '2026-09-20'}, format='json')
    assert r.status_code == 201

def test_settlement_update_cannot_repoint_to_cancelled_order(db, admin_client):
    """结算 update 改挂明细到已取消订单 → 400（与 create 同规则）"""
    f = Factory.objects.create(name='华鑫Y')
    c1 = Customer.objects.create(name='正常Y')
    o1 = Order.objects.create(order_no='OY1', tracking_status='排产', customer=c1, amount_usd='100')
    i1 = OrderItem.objects.create(order=o1, seq=1, factory=f, qty=1, subtotal='100', cost_price='50')
    c2 = Customer.objects.create(name='取消Y')
    o2 = Order.objects.create(order_no='OY2', tracking_status='已取消', is_cancelled=True, customer=c2, amount_usd='100')
    i2 = OrderItem.objects.create(order=o2, seq=1, factory=f, qty=1, subtotal='100', cost_price='50')
    r = admin_client.post('/api/factory-payment/payments/', {
        'order_item': i1.id, 'factory': f.id, 'amount_cny': '50'}, format='json')
    fid = r.data['data']['id']
    r2 = admin_client.patch(f'/api/factory-payment/payments/{fid}/', {'order_item': i2.id}, format='json')
    assert r2.status_code == 400
