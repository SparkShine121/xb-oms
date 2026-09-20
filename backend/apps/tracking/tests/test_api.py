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

# ---- BUG-SIM-009/016 followup ----

def test_advance_rejects_stale_state(db, admin_client, monkeypatch):
    """指纹校验：请求读取后状态被他人推进 → 400 变更拒绝（防双击双推）"""
    from apps.tracking.views import TrackingViewSet
    from apps.tracking.services import advance_order
    from rest_framework.exceptions import ValidationError
    from apps.orders.models import Order as O
    o = O.objects.create(order_no='OADV', tracking_status='接单')
    # 模拟并发：请求 A 已读到旧对象（stale），请求 B 两次推进并提交（save 才触发 updated_at）
    b1 = O.objects.get(pk=o.pk); b1.tracking_status = '排产'
    b1.save(update_fields=['tracking_status', 'updated_at'])  # 模拟并发服务（会刷新指纹）
    stale = O.objects.get(pk=o.pk)  # 请求 A 的读取点（指纹=排产时刻）
    b2 = O.objects.get(pk=o.pk); b2.tracking_status = '生产中'
    b2.save(update_fields=['tracking_status', 'updated_at'])
    with pytest.raises(ValidationError):
        advance_order(stale, None, '', [])
    o.refresh_from_db()
    assert o.tracking_status == '生产中'  # 旧请求被拒，状态未被旧请求改动

def test_advance_service_normal_flow(db, admin_client):
    """回归锁：service 层正常推进 + 视图行为一致"""
    from apps.tracking.services import advance_order
    from apps.orders.models import Order as O
    o = O.objects.create(order_no='ONRM', tracking_status='接单')
    fresh, node = advance_order(O.objects.get(pk=o.pk), None, '', [])
    assert node == '排产'
    o.refresh_from_db()
    assert o.tracking_status == '排产'
