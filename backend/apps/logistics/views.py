from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from apps.logistics.models import Logistics
from apps.logistics.serializers import LogisticsSerializer
from common.views import BaseModelViewSet

from .permissions import LogisticsPermission


class LogisticsViewSet(BaseModelViewSet):
    """物流发货记录 CRUD。

    数据范围：admin/finance 全量；salesman 看自己客户的订单发货；
    tracker 看派给自己的订单发货。写权限见 LogisticsPermission。
    """

    serializer_class = LogisticsSerializer
    permission_classes = [IsAuthenticated, LogisticsPermission]
    filterset_fields = ['payer', 'cost_currency']
    search_fields = ['tracking_no', 'order__order_no']
    ordering_fields = ['seq', 'created_at']
    ordering = ['order', 'seq']

    def get_queryset(self):
        u = self.request.user
        groups = set(u.groups.values_list('name', flat=True))
        qs = Logistics.objects.select_related('order', 'domestic_carrier', 'intl_method')
        if 'admin' in groups or 'finance' in groups:
            return qs
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(order__customer__salesman=u)
        if 'tracker' in groups:
            cond |= Q(order__tracker=u)
        return qs.filter(cond).distinct() if cond else qs.none()
