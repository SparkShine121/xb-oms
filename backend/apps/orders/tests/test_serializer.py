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