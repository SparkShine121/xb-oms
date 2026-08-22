import pytest
from django.core.exceptions import ValidationError

from apps.logistics.models import Logistics
from apps.orders.models import Order
from apps.basic_info.models import Customer, LogisticsProvider

@pytest.fixture
def setup(db):
    c = Customer.objects.create(name='客户A')
    o = Order.objects.create(order_no='O1', customer=c)
    domestic = LogisticsProvider.objects.create(name='顺丰', type='domestic')
    intl = LogisticsProvider.objects.create(name='DHL', type='international')
    return {'order': o, 'domestic': domestic, 'intl': intl}

def test_seq_auto_increment(setup):
    s = setup
    s1 = Logistics.objects.create(order=s['order'], domestic_carrier=s['domestic'])
    assert s1.seq == 1

    s2 = Logistics.objects.create(order=s['order'], intl_method=s['intl'], tracking_no='SF123')
    assert s2.seq == 2

    # 再次保存（更新）不应改变 seq
    s1.tracking_no = 'SF999'
    s1.save()
    s1.refresh_from_db()
    assert s1.seq == 1

def test_payer_choices_validation(setup):
    s = setup
    shipment = Logistics.objects.create(order=s['order'])
    shipment.payer = 'invalid_payer'
    with pytest.raises(ValidationError):
        shipment.full_clean()

def test_currency_and_payer_defaults(setup):
    s = setup
    shipment = Logistics.objects.create(order=s['order'])
    assert shipment.cost_currency == 'CNY'
    assert shipment.payer == 'company'
    assert str(shipment.cost) == '0' or shipment.cost == 0

    # payer 可设为 customer / factory
    shipment.payer = 'customer'
    shipment.full_clean()
    shipment.payer = 'factory'
    shipment.full_clean()
