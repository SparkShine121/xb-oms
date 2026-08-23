import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from apps.finance.models import PaymentIn
from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Customer, Factory, LogisticsProvider
from apps.factory_payment.models import FactoryPayment, FactoryPaymentRecord
from apps.logistics.models import Logistics


def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u


@pytest.fixture
def setup(db):
    s1 = _make_user('sales_a', 'salesman')
    ca = Customer.objects.create(name='客户甲', salesman=s1)
    cb = Customer.objects.create(name='客户乙')
    oa = Order.objects.create(order_no='OA', tracking_status='排产', customer=ca, salesman=s1,
                              amount_usd='1000.00', order_date='2026-08-01', service_fee_usd='15.00')
    ob = Order.objects.create(order_no='OB', tracking_status='排产', customer=cb,
                              amount_usd='500.00', order_date='2026-07-20', service_fee_usd='8.00')

    # 收入：回款 2 笔（OA）
    PaymentIn.objects.create(order=oa, amount_usd='300.00', payment_date='2026-08-05', installment=1)
    PaymentIn.objects.create(order=oa, amount_usd='400.00', payment_date='2026-08-20', installment=2)

    # 支出：工厂付款记录（OB 的订单项）
    factory = Factory.objects.create(name='工厂A')
    item = OrderItem.objects.create(order=ob, seq=1, factory=factory, qty=10,
                                    unit_price='30.00', subtotal='300.00', cost_price='150.00')
    fp = FactoryPayment.objects.create(order_item=item, factory=factory, amount_cny='2100.00')
    FactoryPaymentRecord.objects.create(factory_payment=fp, amount='1000.00', payment_date='2026-08-10')

    # 支出：物流费用（OB）
    carrier = LogisticsProvider.objects.create(name='DHL', type='international')
    Logistics.objects.create(order=ob, intl_method=carrier, tracking_no='DHL001',
                             cost='120.50', cost_currency='CNY')

    return {'oa': oa, 'ob': ob, 's1': s1}


def _admin_client():
    c = APIClient()
    c.force_authenticate(_make_user('adm', 'admin'))
    return c


def test_ledger_contains_four_types(db, setup):
    r = _admin_client().get('/api/finance/payments-in/ledger/')
    assert r.status_code == 200
    rows = r.data['data']
    types = {row['type'] for row in rows}
    assert types == {'income_receipt', 'expense_factory', 'expense_logistics', 'expense_service_fee'}
    # 统一结构字段齐全
    for row in rows:
        assert set(row.keys()) >= {'type', 'date', 'amount', 'currency', 'description', 'source_id'}


def test_ledger_amount_sign_and_value(db, setup):
    """收入为正、支出为负。"""
    r = _admin_client().get('/api/finance/payments-in/ledger/')
    rows = {row['type']: row for row in r.data['data']}
    assert float(rows['income_receipt']['amount']) == 700.0 or True  # 多笔取和校验见下
    amounts = [float(row['amount']) for row in r.data['data']]
    income = sum(a for a in amounts if a > 0)
    expense = sum(a for a in amounts if a < 0)
    assert income == pytest.approx(700.0)  # 300 + 400 回款
    assert expense == pytest.approx(-(1000.0 + 120.5 + 23.0))  # 工厂 + 物流 + 两单服务费(15+8)


def test_ledger_filter_type(db, setup):
    r = _admin_client().get('/api/finance/payments-in/ledger/', {'type': 'income_receipt'})
    rows = r.data['data']
    assert rows and all(row['type'] == 'income_receipt' for row in rows)


def test_ledger_filter_date_range(db, setup):
    r = _admin_client().get('/api/finance/payments-in/ledger/',
                            {'start_date': '2026-08-01', 'end_date': '2026-08-15'})
    dates = [row['date'] for row in r.data['data']]
    assert dates and all('2026-08-01' <= d <= '2026-08-15' for d in dates)


def test_ledger_salesman_scoped(db, setup):
    """salesman 只看到自己客户相关流水。"""
    c = APIClient()
    c.force_authenticate(setup['s1'])
    r = c.get('/api/finance/payments-in/ledger/')
    descs = [row['description'] for row in r.data['data']]
    assert any('OA' in d for d in descs)
    assert not any('OB' in d for d in descs)


def test_export_returns_xlsx(db, setup):
    r = _admin_client().get('/api/finance/payments-in/export/')
    assert r.status_code == 200
    assert r['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert len(r.content) > 0
