import pytest
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