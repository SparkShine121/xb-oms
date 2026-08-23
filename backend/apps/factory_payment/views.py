from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Sum
from common.views import BaseModelViewSet
from common.response import success_response, error_response
from apps.orders.models import Order, OrderItem
from apps.system_mgmt.models import ApprovalRequest
from .models import FactoryPayment, FactoryPaymentRecord
from .serializers import FactoryPaymentSerializer, FactoryPaymentRecordSerializer
from .permissions import FactoryPaymentPermission

class FactoryPaymentViewSet(BaseModelViewSet):
    serializer_class = FactoryPaymentSerializer
    permission_classes = [IsAuthenticated, FactoryPaymentPermission]
    filterset_fields = ['factory', 'status']
    search_fields = ['order_item__order__order_no', 'factory__name']
    ordering_fields = ['id', 'created_at', 'amount_cny', 'paid_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        u = self.request.user
        groups = set(u.groups.values_list('name', flat=True))
        qs = FactoryPayment.objects.select_related('order_item__order', 'factory')
        if 'admin' not in groups and 'finance' not in groups:
            cond = Q()
            if 'salesman' in groups:
                cond |= Q(order_item__order__customer__salesman=u)
            if 'tracker' in groups:
                cond |= Q(order_item__order__tracker=u)
            qs = qs.filter(cond).distinct() if cond else qs.none()

        # 日期范围过滤（列表 + statement 共用；filterset_fields 不支持范围，手动过滤）
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        return qs

    def perform_create(self, serializer):
        # 审批流：非 admin 新建 → 挂起待审批；admin 新建 → 直接生效
        instance = serializer.save(is_approved=False)
        if self.request.user.groups.filter(name='admin').exists():
            instance.is_approved = True
            instance.save(update_fields=['is_approved'])
        else:
            ApprovalRequest.objects.create(
                approval_type='settlement', target_id=instance.id,
                target_model='FactoryPayment', submitted_by=self.request.user)

    @action(detail=False, methods=['post'], url_path=r'orders/(?P<order_id>\d+)/generate')
    def generate_by_order(self, request, order_id=None):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return error_response(1004, '订单不存在', status=404)
        items = order.items.filter(factory__isnull=False)
        created, skipped = 0, 0
        with transaction.atomic():
            for item in items:
                if hasattr(item, 'factory_payment'):
                    skipped += 1
                    continue
                FactoryPayment.objects.create(
                    order_item=item, factory=item.factory,
                    amount_cny=item.qty * item.cost_price
                )
                created += 1
        return success_response({'created_count': created, 'skipped_count': skipped})

    @action(detail=False, methods=['get'], url_path='statement')
    def statement(self, request):
        qs = self.get_queryset()
        factory_id = request.query_params.get('factory')
        if factory_id:
            qs = qs.filter(factory_id=factory_id)
        total_amount = qs.aggregate(t=Sum('amount_cny'))['t'] or 0
        total_paid = qs.aggregate(t=Sum('paid_amount'))['t'] or 0
        return success_response({
            'total_amount': str(total_amount),
            'total_paid': str(total_paid),
            'total_unpaid': str(total_amount - total_paid),
            'count': qs.count(),
        })

class FactoryPaymentRecordViewSet(BaseModelViewSet):
    serializer_class = FactoryPaymentRecordSerializer
    permission_classes = [IsAuthenticated, FactoryPaymentPermission]
    filterset_fields = ['factory_payment']
    ordering = ['-created_at']

    def get_queryset(self):
        u = self.request.user
        groups = set(u.groups.values_list('name', flat=True))
        qs = FactoryPaymentRecord.objects.select_related(
            'factory_payment__order_item__order', 'factory_payment__factory'
        )
        if 'admin' in groups or 'finance' in groups:
            return qs
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(factory_payment__order_item__order__customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(factory_payment__order_item__order__tracker=u)
        return qs.filter(cond).distinct() if cond else qs.none()

    def perform_create(self, serializer):
        with transaction.atomic():
            # Record.save() 已自动聚合：records 求和 → 父单 paid_amount → 父单 save() 重算 status
            # 审批流：非 admin 新建付款记录 → 挂起待审批；admin 新建 → 直接生效
            instance = serializer.save(is_approved=False)
            if self.request.user.groups.filter(name='admin').exists():
                instance.is_approved = True
                instance.save(update_fields=['is_approved'])
            else:
                ApprovalRequest.objects.create(
                    approval_type='payment', target_id=instance.id,
                    target_model='FactoryPaymentRecord', submitted_by=self.request.user)
