"""数据分析聚合 API 测试（Task 5）。

覆盖 4 个端点：
- GET /api/analytics/sales/          销售结算表（按业务员聚合 + 月度趋势）
- GET /api/analytics/factory-summary/ 工厂账单汇总（应付/已付/未付）
- GET /api/analytics/tracking-summary/ 跟单汇总（节点分布 + 平均停留时长）
- GET /api/analytics/overview/       年度总览（总额 + 月度趋势）
"""

import pytest
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.basic_info.models import Factory
from apps.factory_payment.models import FactoryPayment
from apps.tracking.models import TrackingLog


@pytest.fixture
def api(db):
    u = User.objects.create_user('boss', password='pw123456')
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.fixture
def s1(db):
    return User.objects.create_user('salesman1', password='pw123456')


@pytest.fixture
def s2(db):
    return User.objects.create_user('salesman2', password='pw123456')


def make_order(**kw):
    defaults = dict(
        order_no='O-X',
        order_date=date(2026, 7, 10),
        amount_usd='1000',
        order_profit_usd='200',
    )
    defaults.update(kw)
    return Order.objects.create(**defaults)


# ---------- 认证 ----------

def test_all_endpoints_require_auth(db):
    c = APIClient()
    assert c.get('/api/analytics/sales/').status_code == 401
    assert c.get('/api/analytics/factory-summary/').status_code == 401
    assert c.get('/api/analytics/tracking-summary/').status_code == 401
    assert c.get('/api/analytics/overview/').status_code == 401


# ---------- sales 销售结算表 ----------

def test_sales_summary_groups_by_salesman(api, db, s1, s2):
    make_order(order_no='A1', salesman=s1, amount_usd='1000', order_profit_usd='200')
    make_order(order_no='A2', salesman=s1, amount_usd='3000', order_profit_usd='600')
    make_order(order_no='B1', salesman=s2, amount_usd='500', order_profit_usd='50')

    r = api.get('/api/analytics/sales/')
    assert r.status_code == 200
    assert r.data['code'] == 0

    rows = {x['salesman__username']: x for x in r.data['data']['by_salesman']}
    assert rows['salesman1']['order_count'] == 2
    assert rows['salesman1']['total_amount'] == 4000
    assert rows['salesman1']['total_profit'] == 800
    assert rows['salesman1']['profit_rate'] == pytest.approx(0.2)
    assert rows['salesman2']['order_count'] == 1
    assert rows['salesman2']['total_amount'] == 500


def test_sales_summary_excludes_cancelled_and_supports_filters(api, db, s1, s2):
    make_order(order_no='A1', salesman=s1, order_date=date(2026, 7, 10))
    make_order(order_no='C1', salesman=s1, is_cancelled=True)
    make_order(order_no='D1', salesman=s2, order_date=date(2025, 3, 1))

    r = api.get('/api/analytics/sales/?year=2026')
    rows = r.data['data']['by_salesman']
    assert len(rows) == 1
    assert rows[0]['salesman__username'] == 'salesman1'

    r2 = api.get(f'/api/analytics/sales/?salesman={s2.id}')
    rows2 = r2.data['data']['by_salesman']
    assert len(rows2) == 1
    assert rows2[0]['salesman__username'] == 'salesman2'


def test_sales_summary_monthly_trend(api, db):
    make_order(order_no='M1', order_date=date(2026, 7, 10), amount_usd='100', order_profit_usd='20')
    make_order(order_no='M2', order_date=date(2026, 8, 5), amount_usd='300', order_profit_usd='60')

    r = api.get('/api/analytics/sales/')
    months = {m['month']: m for m in r.data['data']['monthly']}
    assert months['2026-07']['sales'] == 100
    assert months['2026-07']['count'] == 1
    assert months['2026-08']['profit'] == 60


# ---------- factory-summary 工厂账单汇总 ----------

@pytest.fixture
def fp_setup(db):
    f1 = Factory.objects.create(name='工厂甲')
    f2 = Factory.objects.create(name='工厂乙')
    o = Order.objects.create(order_no='FP1')
    item1 = OrderItem.objects.create(order=o, seq=1)
    item2 = OrderItem.objects.create(order=o, seq=2)
    item3 = OrderItem.objects.create(order=o, seq=3)
    FactoryPayment.objects.create(order_item=item1, factory=f1, amount_cny='1000', paid_amount='400')
    FactoryPayment.objects.create(order_item=item2, factory=f1, amount_cny='500', paid_amount='500')
    FactoryPayment.objects.create(order_item=item3, factory=f2, amount_cny='800', paid_amount='0')
    return f1, f2


def test_factory_summary_aggregates_by_factory(api, db, fp_setup):
    r = api.get('/api/analytics/factory-summary/')
    assert r.status_code == 200
    assert r.data['code'] == 0

    rows = {x['factory__name']: x for x in r.data['data']}
    jia = rows['工厂甲']
    assert jia['total_amount'] == 1500
    assert jia['total_paid'] == 900
    assert jia['total_unpaid'] == 600
    assert jia['payment_count'] == 2
    yi = rows['工厂乙']
    assert yi['total_paid'] == 0
    assert yi['total_unpaid'] == 800


def test_factory_summary_ordered_by_amount_desc(api, db, fp_setup):
    r = api.get('/api/analytics/factory-summary/')
    amounts = [x['total_amount'] for x in r.data['data']]
    assert amounts == sorted(amounts, reverse=True)


def test_factory_summary_filter_by_factory(api, db, fp_setup):
    _, f2 = fp_setup
    r = api.get(f'/api/analytics/factory-summary/?factory={f2.id}')
    assert len(r.data['data']) == 1
    assert r.data['data'][0]['factory__name'] == '工厂乙'


# ---------- tracking-summary 跟单信息汇总 ----------

def test_tracking_summary_node_distribution(api, db):
    Order.objects.create(order_no='T1', tracking_status='接单')
    Order.objects.create(order_no='T2', tracking_status='接单')
    Order.objects.create(order_no='T3', tracking_status='生产中')
    Order.objects.create(order_no='T4', tracking_status='已取消', is_cancelled=True)

    r = api.get('/api/analytics/tracking-summary/')
    assert r.status_code == 200
    assert r.data['code'] == 0

    dist = {x['node']: x['count'] for x in r.data['data']['node_distribution']}
    assert dist['接单'] == 2
    assert dist['生产中'] == 1
    assert '已取消' not in dist


def test_tracking_summary_avg_dwell_days(api, db):
    o = Order.objects.create(order_no='DW1', tracking_status='排产')
    now = timezone.now()
    l1 = TrackingLog.objects.create(order=o, node='接单')
    l2 = TrackingLog.objects.create(order=o, node='排产')
    # auto_now_add 字段用 queryset.update 回填历史时间
    TrackingLog.objects.filter(id=l1.id).update(created_at=now - timedelta(days=2))
    TrackingLog.objects.filter(id=l2.id).update(created_at=now - timedelta(days=1))

    r = api.get('/api/analytics/tracking-summary/')
    dwell = {x['node']: x['avg_days'] for x in r.data['data']['avg_dwell_days']}
    assert dwell['接单'] == pytest.approx(1.0)


# ---------- overview 年度总览 ----------

def test_overview_totals_and_monthly_trend(api, db):
    make_order(order_no='OV1', order_date=date(2026, 7, 10), amount_usd='1000', order_profit_usd='200')
    make_order(order_no='OV2', order_date=date(2026, 7, 20), amount_usd='500', order_profit_usd='100')
    make_order(order_no='OV3', order_date=date(2026, 8, 1), amount_usd='300', order_profit_usd='-50')
    make_order(order_no='OVX', order_date=date(2026, 8, 2), amount_usd='999',
               order_profit_usd='99', is_cancelled=True)

    r = api.get('/api/analytics/overview/?year=2026')
    assert r.status_code == 200
    assert r.data['code'] == 0
    d = r.data['data']

    assert d['total_orders'] == 3
    assert d['total_sales'] == 1800
    assert d['total_profit'] == 250

    months = [m['month'] for m in d['monthly']]
    assert months == ['2026-07', '2026-08']  # 升序
    jul = d['monthly'][0]
    assert jul['sales'] == 1500
    assert jul['profit'] == 300
