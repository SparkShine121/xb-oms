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

def test_generate_by_order(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.count() == 1
    fp = FactoryPayment.objects.first()
    assert str(fp.amount_cny) == '72.00'

def test_generate_skips_existing(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.post(f'/api/factory-payment/payments/orders/{o.id}/generate/', format='json')
    assert r.status_code == 200
    assert FactoryPayment.objects.count() == 1

def test_payment_record_updates_status(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    fp = FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.post('/api/factory-payment/records/', {
        'factory_payment': fp.id, 'amount': '30.00', 'payment_date': '2026-08-14'
    }, format='json')
    assert r.status_code == 201
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '30.00'
    assert fp.status == '部分结'

def test_statement(db, admin_client):
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00')
    r = admin_client.get('/api/factory-payment/payments/statement/', {'factory': f.id})
    assert r.status_code == 200
    assert 'total_amount' in r.data['data']


@pytest.fixture
def finance_client(db):
    u = User.objects.create_user('fin1', password='pw123456')
    u.groups.add(Group.objects.get(name='finance'))
    c = APIClient(); c.force_authenticate(u); return c


def _approved_settlement():
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', tracking_status='排产', customer=c, amount_usd='100')
    item = OrderItem.objects.create(order=o, seq=1, factory=f, qty=10, unit_price='10', subtotal='100', cost_price='7.20')
    return FactoryPayment.objects.create(order_item=item, factory=f, amount_cny='72.00', is_approved=True)


# ---- 收尾批：FP/FPRecord 打回泛化（BUG-SIM-024 同规则）----

def test_finance_edit_approved_payment_recoils(db, finance_client):
    """finance 编辑已批准结算单 → 打回未批准 + 重挂 settlement 审批"""
    from apps.system_mgmt.models import ApprovalRequest
    fp = _approved_settlement()
    r = finance_client.patch(f'/api/factory-payment/payments/{fp.id}/', {'note': '调整'}, format='json')
    assert r.status_code == 200
    fp.refresh_from_db()
    assert fp.is_approved is False
    assert ApprovalRequest.objects.filter(
        approval_type='settlement', target_model='FactoryPayment',
        target_id=fp.id, status='pending').exists()

def test_admin_edit_approved_payment_no_recoil(db, admin_client):
    """admin 编辑已批准结算单不打回（admin 即审批人）"""
    from apps.system_mgmt.models import ApprovalRequest
    fp = _approved_settlement()
    r = admin_client.patch(f'/api/factory-payment/payments/{fp.id}/', {'note': '调整'}, format='json')
    assert r.status_code == 200
    fp.refresh_from_db()
    assert fp.is_approved is True
    assert not ApprovalRequest.objects.filter(
        target_model='FactoryPayment', target_id=fp.id).exists()

def test_finance_edit_approved_record_recoils(db, finance_client):
    """finance 编辑已批准付款记录 → 打回 + 重挂 payment 审批 + 父单已付重聚合"""
    from apps.system_mgmt.models import ApprovalRequest
    fp = _approved_settlement()
    rec = FactoryPaymentRecord.objects.create(
        factory_payment=fp, amount='30.00', payment_date='2026-08-14', is_approved=True)
    fp.refresh_from_db()
    assert str(fp.paid_amount) == '30.00'  # 前置：已批准记录计入已付
    r = finance_client.patch(f'/api/factory-payment/records/{rec.id}/', {'amount': '35.00'}, format='json')
    assert r.status_code == 200
    rec.refresh_from_db(); fp.refresh_from_db()
    assert rec.is_approved is False
    assert ApprovalRequest.objects.filter(
        approval_type='payment', target_model='FactoryPaymentRecord',
        target_id=rec.id, status='pending').exists()
    assert str(fp.paid_amount) == '0.00'  # 打回后父单重聚合，不含编辑中的付款
    assert fp.status == '未结'

def test_admin_edit_approved_record_no_recoil(db, admin_client):
    """admin 编辑已批准付款记录不打回，已付含新值"""
    from apps.system_mgmt.models import ApprovalRequest
    fp = _approved_settlement()
    rec = FactoryPaymentRecord.objects.create(
        factory_payment=fp, amount='30.00', payment_date='2026-08-14', is_approved=True)
    r = admin_client.patch(f'/api/factory-payment/records/{rec.id}/', {'amount': '35.00'}, format='json')
    assert r.status_code == 200
    rec.refresh_from_db(); fp.refresh_from_db()
    assert rec.is_approved is True
    assert str(fp.paid_amount) == '35.00'
    assert not ApprovalRequest.objects.filter(
        target_model='FactoryPaymentRecord', target_id=rec.id).exists()
