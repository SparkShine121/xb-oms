import pytest
from django.contrib.auth.models import User
from apps.tracking.models import TrackingLog, TrackingPhoto
from apps.orders.models import Order

def test_tracking_log(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    log = TrackingLog.objects.create(order=o, node='排产', note='开始排产', operator=u, is_reject=False)
    assert log.node == '排产' and log.is_reject is False
    assert log.order == o

def test_tracking_photo(db):
    from django.core.files.uploadedfile import SimpleUploadedFile
    u = User.objects.create_user('tracker1', password='pw123456')
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    log = TrackingLog.objects.create(order=o, node='排产', operator=u)
    photo = TrackingPhoto.objects.create(tracking_log=log, image=SimpleUploadedFile('test.jpg', b'\x47\x49\x46\x38', content_type='image/jpeg'))
    assert photo.tracking_log == log
    assert log.photos.count() == 1
