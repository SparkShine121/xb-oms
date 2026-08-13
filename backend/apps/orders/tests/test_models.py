import pytest
from datetime import date
from django.contrib.auth.models import User
from apps.basic_info.models import Customer
from apps.orders.models import ExchangeRate

def test_customer_tracker(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    c = Customer.objects.create(name='客户A', tracker=u)
    assert c.tracker == u

def test_exchange_rate_effective(db):
    from datetime import date
    ExchangeRate.objects.create(currency_pair='USD/CNY', rate='7.20', effective_date=date(2026,7,1))
    ExchangeRate.objects.create(currency_pair='USD/CNY', rate='7.15', effective_date=date(2026,8,1))
    assert str(ExchangeRate.get_effective_rate(date(2026,7,15)).rate) == '7.2000'
    assert str(ExchangeRate.get_effective_rate(date(2026,8,10)).rate) == '7.1500'
    assert ExchangeRate.get_effective_rate(date(2026,6,1)) is None


@pytest.fixture
def rate(db):
    return ExchangeRate.objects.create(currency_pair='USD/CNY', rate='7.20', effective_date=date(2026,1,1))

def test_order_with_items_profit(db, rate):
    from apps.orders.models import Order, OrderItem, calc_order_profit
    from apps.basic_info.models import Customer
    from datetime import date
    c = Customer.objects.create(name='C1')
    o = Order.objects.create(order_no='O1', order_date=date(2026,7,15), customer=c, amount_usd='100', freight='10', insurance='5', surcharge='5', service_fee_usd='2')
    OrderItem.objects.create(order=o, seq=1, qty=10, unit_price='10', subtotal='100', cost_price='72')
    # 产品毛利 = 100 - 72*10/7.20 = 100 - 100 = 0；订单毛利 = 0 - 10 - 5 - 5 - 2 = -22
    calc_order_profit(o)
    assert str(o.order_profit_usd) == '-22.00'
    item = o.items.first()
    assert str(item.profit_usd) == '0.00'
    assert str(item.profit_rate) == '0.0000'