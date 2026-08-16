import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from apps.orders.models import Order
from apps.tracking.models import TrackingLog

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c, u

def test_advance_creates_log(db, admin_client):
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '排产开始'}, format='multipart')
    assert r.status_code == 200
    assert TrackingLog.objects.filter(order=o, node='排产', is_reject=False).count() == 1

def test_reject_creates_log(db, admin_client):
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='排产')
    r = c.post(f'/api/tracking/orders/{o.id}/reject/', {'note': '退回接单'}, format='multipart')
    assert r.status_code == 200
    o.refresh_from_db()
    assert o.tracking_status == '接单'
    assert TrackingLog.objects.filter(order=o, node='接单', is_reject=True).count() == 1

def test_timeline(db, admin_client):
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='排产')
    c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '推进'}, format='multipart')
    r = c.get(f'/api/tracking/orders/{o.id}/timeline/')
    assert r.status_code == 200
    assert len(r.data['data']) >= 1

def test_my_workbench(db):
    u = User.objects.create_user('tracker1', password='pw123456')
    u.groups.add(Group.objects.get(name='tracker'))
    Order.objects.create(order_no='O1', tracking_status='接单', tracker=u)
    Order.objects.create(order_no='O2', tracking_status='接单')  # 不是自己的
    c = APIClient(); c.force_authenticate(u)
    r = c.get('/api/tracking/my/')
    assert r.status_code == 200
    assert len(r.data['data']['results']) == 1
    assert r.data['data']['results'][0]['order_no'] == 'O1'

def test_advance_with_photos(db, admin_client):
    from django.core.files.uploadedfile import SimpleUploadedFile
    import io
    from PIL import Image
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'white').save(buf, format='JPEG')  # 真实小图，Pillow verify 会接受
    photo = SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'note': '带照片', 'photos': [photo]}, format='multipart')
    assert r.status_code == 200
    log = TrackingLog.objects.filter(order=o).first()
    assert log.photos.count() == 1

def test_advance_photo_invalid(db, admin_client):
    from django.core.files.uploadedfile import SimpleUploadedFile
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    # 伪造 content_type=image/jpeg 的非图片文件（如 xss.html），必须被 Pillow verify 拒绝
    fake = SimpleUploadedFile('xss.html', b'<script>x</script>', content_type='image/jpeg')
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'photos': [fake]}, format='multipart')
    assert r.status_code == 400
    assert TrackingLog.objects.filter(order=o).count() == 0

def test_advance_photo_too_large(db, admin_client):
    from django.core.files.uploadedfile import SimpleUploadedFile
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    big = SimpleUploadedFile('big.jpg', b'\x00' * (5 * 1024 * 1024 + 1), content_type='image/jpeg')
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'photos': [big]}, format='multipart')
    assert r.status_code == 400
    assert TrackingLog.objects.filter(order=o).count() == 0

def test_advance_too_many_photos(db, admin_client):
    from django.core.files.uploadedfile import SimpleUploadedFile
    c, _ = admin_client
    o = Order.objects.create(order_no='O1', tracking_status='接单')
    photos = [SimpleUploadedFile(f'p{i}.jpg', b'\xff\xd8\xff\xe0', content_type='image/jpeg') for i in range(10)]
    r = c.post(f'/api/tracking/orders/{o.id}/advance/', {'photos': photos}, format='multipart')
    assert r.status_code == 400
    assert TrackingLog.objects.filter(order=o).count() == 0
