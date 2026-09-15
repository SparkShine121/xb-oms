import pytest
from apps.orders.serializers import OrderSerializer
from apps.orders.models import Order, ExchangeRate
from apps.basic_info.models import Customer
from datetime import date

@pytest.fixture
def rate(db):
    return ExchangeRate.objects.create(currency_pair='USD/CNY', rate='7.20', effective_date=date(2026,1,1))

def test_create_order_with_items(db, rate):
    c = Customer.objects.create(name='C1')
    data = {'order_no':'O1','order_date':'2026-07-15','customer':c.id,'amount_usd':'100','freight':'10','items':[
        {'seq':1,'qty':10,'unit_price':'10','subtotal':'100','cost_price':'72'}]}
    s = OrderSerializer(data=data)
    assert s.is_valid(), s.errors
    o = s.save()
    assert o.order_no == 'O1'
    assert o.items.count() == 1
    # 毛利触发：订单毛利 = 0 - 10 - 0 - 0 - 0 = -10（insurance/surcharge/service_fee 默认0）
    assert str(o.order_profit_usd) == '-10.00'

def test_update_order_replaces_items(db, rate):
    c = Customer.objects.create(name='C1')
    o = Order.objects.create(order_no='O1', amount_usd='100', freight='10')
    from apps.orders.models import OrderItem
    OrderItem.objects.create(order=o, seq=1, qty=1, subtotal='50', cost_price='36')
    data = {'items':[{'seq':1,'qty':2,'subtotal':'80','cost_price':'57.6'}]}
    s = OrderSerializer(o, data=data, partial=True)
    assert s.is_valid(), s.errors
    s.save()
    assert o.items.count() == 1  # 整组替换
# ---- BUG-SIM-002: 明细 diff 更新 + 结算数据保护 ----
from rest_framework.exceptions import ValidationError
from apps.factory_payment.models import FactoryPayment
from apps.basic_info.models import Factory
from apps.orders.models import OrderItem


def _settled_order():
    """订单 O1：明细 P1（无结算）、P2（挂结算单 fp）"""
    f = Factory.objects.create(name='华鑫')
    c = Customer.objects.create(name='C1')
    o = Order.objects.create(order_no='O1', amount_usd='100', freight='10')
    ia = OrderItem.objects.create(order=o, seq=1, product_no='P1', qty=10, unit_price='10', subtotal='100', cost_price='72')
    ib = OrderItem.objects.create(order=o, seq=2, product_no='P2', qty=5, unit_price='20', subtotal='100', cost_price='50')
    fp = FactoryPayment.objects.create(order_item=ib, factory=f, amount_cny='72.00')
    return o, ia, ib, fp


def test_diff_update_keeps_item_ids(db, rate):
    o, ia, ib, fp = _settled_order()
    data = {'items': [
        {'id': ia.id, 'seq': 1, 'product_no': 'P1', 'qty': 10, 'unit_price': '10', 'subtotal': '100', 'cost_price': '72', 'spec': '新规格'},
        {'id': ib.id, 'seq': 2, 'product_no': 'P2', 'qty': 5, 'unit_price': '20', 'subtotal': '100', 'cost_price': '50'},
    ]}
    s = OrderSerializer(o, data=data, partial=True)
    assert s.is_valid(), s.errors
    s.save()
    assert list(o.items.values_list('id', flat=True).order_by('id')) == sorted([ia.id, ib.id])  # id 不变
    ia.refresh_from_db()
    assert ia.spec == '新规格'


def test_delete_settled_item_rejected(db, rate):
    o, ia, ib, fp = _settled_order()
    data = {'items': [{'id': ia.id, 'seq': 1, 'product_no': 'P1', 'qty': 10, 'unit_price': '10', 'subtotal': '100', 'cost_price': '72'}]}
    s = OrderSerializer(o, data=data, partial=True)
    assert s.is_valid(), s.errors
    with pytest.raises(ValidationError):
        s.save()
    assert OrderItem.objects.filter(id=ib.id).exists()
    assert FactoryPayment.objects.filter(id=fp.id).exists()  # 结算+付款记录完好


def test_delete_unsettled_item_allowed(db, rate):
    o, ia, ib, fp = _settled_order()
    data = {'items': [{'id': ib.id, 'seq': 2, 'product_no': 'P2', 'qty': 5, 'unit_price': '20', 'subtotal': '100', 'cost_price': '50'}]}
    s = OrderSerializer(o, data=data, partial=True)
    assert s.is_valid(), s.errors
    s.save()
    assert not OrderItem.objects.filter(id=ia.id).exists()
    assert o.items.count() == 1


def test_amount_frozen_on_settled_item(db, rate):
    o, ia, ib, fp = _settled_order()
    # 改金额 → 拒绝
    data = {'items': [
        {'id': ia.id, 'seq': 1, 'product_no': 'P1', 'qty': 10, 'unit_price': '10', 'subtotal': '100', 'cost_price': '72'},
        {'id': ib.id, 'seq': 2, 'product_no': 'P2', 'qty': 5, 'unit_price': '20', 'subtotal': '120', 'cost_price': '50'},
    ]}
    s = OrderSerializer(o, data=data, partial=True)
    assert s.is_valid(), s.errors
    with pytest.raises(ValidationError):
        s.save()
    ib.refresh_from_db()
    assert str(ib.subtotal) == '100.00'
    assert FactoryPayment.objects.filter(id=fp.id).exists()
    # 改非金额字段（spec）→ 允许
    data2 = {'items': [
        {'id': ia.id, 'seq': 1, 'product_no': 'P1', 'qty': 10, 'unit_price': '10', 'subtotal': '100', 'cost_price': '72'},
        {'id': ib.id, 'seq': 2, 'product_no': 'P2', 'qty': 5, 'unit_price': '20', 'subtotal': '100', 'cost_price': '50', 'spec': '升级版'},
    ]}
    s2 = OrderSerializer(o, data=data2, partial=True)
    assert s2.is_valid(), s2.errors
    s2.save()
    ib.refresh_from_db()
    assert ib.spec == '升级版'


def test_status_only_change_does_not_touch_items(db, rate):
    """路径③治愈：items 带 id 原样提交（或整个不带 items）→ 明细零删除、结算完好"""
    o, ia, ib, fp = _settled_order()
    items_payload = [
        {'id': ia.id, 'seq': 1, 'product_no': 'P1', 'qty': 10, 'unit_price': '10', 'subtotal': '100', 'cost_price': '72'},
        {'id': ib.id, 'seq': 2, 'product_no': 'P2', 'qty': 5, 'unit_price': '20', 'subtotal': '100', 'cost_price': '50'},
    ]
    s = OrderSerializer(o, data={'tracking_status': '排产', 'items': items_payload}, partial=True)
    assert s.is_valid(), s.errors
    s.save()
    assert list(o.items.values_list('id', flat=True)) == [ia.id, ib.id]
    assert FactoryPayment.objects.filter(id=fp.id).exists()
    # 不带 items 的纯状态修改
    s2 = OrderSerializer(o, data={'remark': '仅备注'}, partial=True)
    assert s2.is_valid(), s2.errors
    s2.save()
    assert list(o.items.values_list('id', flat=True)) == [ia.id, ib.id]
