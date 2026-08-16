import pytest
from django.contrib.auth.models import User
from apps.tracking.serializers import TrackingLogSerializer
from apps.tracking.models import TrackingLog
from apps.orders.models import Order

def test_log_serializer_fields(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    log = TrackingLog.objects.create(order=o, node='排产', note='排产中', operator=u, is_reject=False)
    s = TrackingLogSerializer(log)
    assert s.data['node'] == '排产'
    assert s.data['note'] == '排产中'
    assert s.data['is_reject'] is False
    assert s.data['operator_name'] == 'tracker1'
    assert s.data['order_no'] == 'O1'
    assert isinstance(s.data['photos'], list)
