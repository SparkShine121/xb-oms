from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Sum
from common.views import BaseModelViewSet
from common.response import success_response, error_response
from apps.orders.models import Order, OrderItem
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
        if 'admin' in groups or 'finance' in groups:
            return qs
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(order_item__order__customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(order_item__order__tracker=u)
        return qs.filter(cond).distinct() if cond else qs.none()

    @action(detail=False, methods=['post'], url_path=r'orders/(?P<order_id>\d+)/generate')
    def generate_by_order(self, request, order_id=None):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return error_response(1004, '订单不存在', status=404)
        items = order.items.filter(factory__isnull=False)
        created, skipped = 0, 0
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
        return FactoryPaymentRecord.objects.select_related('factory_payment__order_item__order')

    def perform_create(self, serializer):
        with transaction.atomic():
            # Record.save() 已自动聚合：records 求和 → 父单 paid_amount → 父单 save() 重算 status
            serializer.save()
