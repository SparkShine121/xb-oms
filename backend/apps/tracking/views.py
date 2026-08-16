from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.files.uploadedfile import UploadedFile
from common.response import success_response, error_response
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from .models import TrackingLog, TrackingPhoto
from .serializers import TrackingLogSerializer
from .permissions import TrackingPermission
from .state_machine import next_node, prev_node

MAX_PHOTOS = 9
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/jpg'}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB

class TrackingViewSet(ViewSet):
    permission_classes = [IsAuthenticated, TrackingPermission]

    def _get_order_qs(self, request):
        u = request.user
        groups = set(u.groups.values_list('name', flat=True))
        if 'admin' in groups or 'finance' in groups:
            return Order.objects.all()
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(tracker=u)
        return Order.objects.filter(cond).distinct() if cond else Order.objects.none()

    def _get_order(self, request, pk):
        """取订单：先按角色可见范围过滤；范围外但订单存在时仍做对象权限校验（403 vs 404）。"""
        order = self._get_order_qs(request).filter(pk=pk).first()
        if order:
            return order
        raw = Order.objects.filter(pk=pk).first()
        if raw is not None:
            self.check_object_permissions(request, raw)
        return None

    def _validate_photos(self, request):
        photos = request.FILES.getlist('photos')
        if len(photos) > MAX_PHOTOS:
            return None, f'最多 {MAX_PHOTOS} 张照片'
        for p in photos:
            if p.size > MAX_PHOTO_SIZE:
                return None, f'照片 {p.name} 超过 5MB'
            if p.content_type not in ALLOWED_TYPES:
                return None, f'照片 {p.name} 格式不支持（仅 jpg/png）'
        return photos, None

    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        order = self._get_order(request, pk)
        if not order:
            return error_response(1004, '订单不存在', status=404)
        self.check_object_permissions(request, order)
        if order.is_cancelled:
            return error_response(1001, '已取消订单不可流转', status=400)
        node = next_node(order.tracking_status)
        if not node:
            return error_response(1001, '当前节点不可推进（终态）', status=400)
        photos, err = self._validate_photos(request)
        if err:
            return error_response(1001, err, status=400)
        log = TrackingLog.objects.create(order=order, node=node, note=request.data.get('note', ''), operator=request.user, is_reject=False)
        for p in (photos or []):
            TrackingPhoto.objects.create(tracking_log=log, image=p)
        order.tracking_status = node
        order.save(update_fields=['tracking_status'])
        return success_response({'log': TrackingLogSerializer(log, context={'request': request}).data, 'tracking_status': node})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self._get_order(request, pk)
        if not order:
            return error_response(1004, '订单不存在', status=404)
        self.check_object_permissions(request, order)
        if order.is_cancelled:
            return error_response(1001, '已取消订单不可流转', status=400)
        node = prev_node(order.tracking_status)
        if not node:
            return error_response(1001, '当前节点不可驳回（起点）', status=400)
        photos, err = self._validate_photos(request)
        if err:
            return error_response(1001, err, status=400)
        log = TrackingLog.objects.create(order=order, node=node, note=request.data.get('note', ''), operator=request.user, is_reject=True)
        for p in (photos or []):
            TrackingPhoto.objects.create(tracking_log=log, image=p)
        order.tracking_status = node
        order.save(update_fields=['tracking_status'])
        return success_response({'log': TrackingLogSerializer(log, context={'request': request}).data, 'tracking_status': node})

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        order = self._get_order(request, pk)
        if not order:
            return error_response(1004, '订单不存在', status=404)
        self.check_object_permissions(request, order)
        logs = TrackingLog.objects.filter(order=order).order_by('-created_at')
        return success_response(TrackingLogSerializer(logs, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def my(self, request):
        qs = Order.objects.filter(tracker=request.user, is_cancelled=False).order_by('-updated_at')
        from rest_framework.response import Response
        # 简单分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        total = qs.count()
        items = qs[(page-1)*page_size : page*page_size]
        data = []
        for o in items:
            first_log = o.tracking_logs.filter(node=o.tracking_status).order_by('created_at').first()
            from django.utils import timezone
            stay_seconds = (timezone.now() - first_log.created_at).total_seconds() if first_log else 0
            data.append({
                'id': o.id, 'order_no': o.order_no, 'tracking_status': o.tracking_status,
                'customer_name': o.customer.name if o.customer else '',
                'stay_seconds': int(stay_seconds),
                'can_advance': bool(next_node(o.tracking_status)),
                'can_reject': bool(prev_node(o.tracking_status)),
            })
        return success_response({'count': total, 'results': data})
