from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from apps.finance.models import PaymentIn
from apps.finance.serializers import PaymentInSerializer
from common.views import BaseModelViewSet

from .permissions import FinancePermission


class PaymentInViewSet(BaseModelViewSet):
    """回款登记 CRUD。

    数据范围：admin/finance 全量；salesman 看自己客户的订单回款；
    tracker 看派给自己的订单回款。写权限见 FinancePermission。
    """

    serializer_class = PaymentInSerializer
    permission_classes = [IsAuthenticated, FinancePermission]
    filterset_fields = ['order']
    search_fields = ['order__order_no']
    ordering_fields = ['payment_date', 'created_at']
    ordering = ['-payment_date', '-id']

    def get_queryset(self):
        u = self.request.user
        groups = set(u.groups.values_list('name', flat=True))
        qs = PaymentIn.objects.select_related('order')
        if 'admin' in groups or 'finance' in groups:
            return qs
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(order__customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(order__tracker=u)
        return qs.filter(cond).distinct() if cond else qs.none()
