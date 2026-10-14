from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q
from common.views import BaseModelViewSet
from common.response import success_response, error_response
from common.permissions import RolePermission, AdminWriteOthersReadOnly
from apps.system_mgmt.models import ApprovalRequest
from apps.system_mgmt.approval import resubmit_on_update
from .models import Order, ExchangeRate
from .serializers import OrderSerializer, ExchangeRateSerializer
from .permissions import OrderPermission
from .services import ensure_order_deletable
from .importers import import_orders, build_order_template


class OrderViewSet(BaseModelViewSet):
    queryset = Order.objects.all()  # BUG-SIM-026：审计日志取 model 用（get_queryset 优先不受影响）
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, OrderPermission]
    filterset_fields = ['tracking_status', 'salesman', 'tracker', 'is_cancelled']
    search_fields = ['order_no', 'customer__name']
    ordering_fields = ['id', 'order_date', 'updated_at']
    ordering = ['id']

    def get_queryset(self):
        qs = Order.objects.all()
        u = self.request.user
        groups = set(u.groups.values_list('name', flat=True))
        if 'admin' in groups or 'finance' in groups:
            return qs
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(tracker=u)
        return qs.filter(cond).distinct() if cond else qs.none()

    # BUG-SIM-002 Q5:i：挂结算单（含付款记录）的订单禁止删除
    def perform_destroy(self, instance):
        ensure_order_deletable(instance)  # ValidationError → 统一异常处理 400
        instance.delete()

    def validate_bulk_delete(self, obj):
        # 批量删除时冲突对象进 forbidden 清单（复用 BUG-SIM-001 的报告机制）
        try:
            ensure_order_deletable(obj)
        except DRFValidationError:
            return '订单已挂结算单'
        return None

    def perform_create(self, serializer):
        # 审批流：非 admin 新建订单（order_change）→ 挂起待审批；admin 新建 → 直接生效
        instance = serializer.save(is_approved=False)
        if self.request.user.groups.filter(name='admin').exists():
            instance.is_approved = True
            instance.save(update_fields=['is_approved'])
        else:
            ApprovalRequest.objects.create(
                approval_type='order_change', target_id=instance.id,
                target_model='Order', submitted_by=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        # BUG-SIM-024 Q4:a：非 admin 编辑已批准订单 → 打回未批准 + 重新挂审
        # （admin 即审批人不受影响；打回创建的 pending 使 resubmit_on_update 判重跳过）
        if not self.request.user.groups.filter(name='admin').exists() and instance.is_approved:
            instance.is_approved = False
            instance.save(update_fields=['is_approved'])
            ApprovalRequest.objects.create(
                approval_type='order_change', target_id=instance.id,
                target_model='Order', submitted_by=self.request.user)
        resubmit_on_update(self.request.user, instance, 'order_change', 'Order')

    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        f = request.FILES.get('file')
        if not f:
            return error_response(1001, '未上传文件', status=400)
        try:
            result = import_orders(f, request.user)  # BUG-SIM-002 Q7:i：归属校验需要操作者
        except Exception as e:
            return error_response(1001, f'文件解析失败：{e}', status=400)
        # 审批流：非 admin 导入的新建订单 → 挂起待审批；admin 导入直接生效
        # （BUG-SIM-004 后导入仅 admin 可达，此分支为防御性保留）
        if not request.user.groups.filter(name='admin').exists() and False:
            for order_no in result.get('created_order_nos', []):
                try:
                    o = Order.objects.get(order_no=order_no)
                except Order.DoesNotExist:
                    continue
                o.is_approved = False
                o.save(update_fields=['is_approved'])
                ApprovalRequest.objects.create(
                    approval_type='order_change', target_id=o.id,
                    target_model='Order', submitted_by=request.user)
        return success_response(result)

    @action(detail=False, methods=['get'], url_path='import-template')
    def import_template(self, request):
        buf = build_order_template()
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename=order_import_template.xlsx'
        return resp

    @action(detail=True, methods=['post'], url_path='set-tracker')
    def set_tracker(self, request, pk=None):
        order = self.get_object()
        tracker_id = request.data.get('tracker')
        from django.contrib.auth.models import User
        try:
            tracker = User.objects.get(pk=tracker_id)
        except User.DoesNotExist:
            return error_response(1004, '用户不存在', status=404)
        # BUG-SIM-014 Q3:a：派单目标必须为 tracker 角色
        if not tracker.groups.filter(name='tracker').exists():
            return error_response(1001, '目标用户必须为跟单员（tracker）角色', status=400)
        order.tracker = tracker; order.save()
        return success_response(OrderSerializer(order).data)


def _recalc_affected_orders():
    """BUG-SIM-022 Q2:a：汇率变更后全量批量重算订单毛利（bulk_update，约 5 条查询）。"""
    from apps.orders.models import recalc_all_orders
    recalc_all_orders()


class ExchangeRateViewSet(BaseModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    # BUG-SIM-022 Q1:a：全员可读、仅 admin 可写（原 RolePermission 空 roles 致 finance 读也 403）
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]

    def perform_create(self, serializer):
        # 事务包裹：汇率保存与全量重算原子化（重算失败整体回滚，无半一致状态）
        with transaction.atomic():
            instance = serializer.save()
            _recalc_affected_orders()

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            _recalc_affected_orders()

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.delete()
            _recalc_affected_orders()