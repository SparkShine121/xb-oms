from django.db.models import Q
from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.factory_payment.models import FactoryPaymentRecord
from apps.finance.models import PaymentIn
from apps.finance.serializers import PaymentInSerializer
from apps.logistics.models import Logistics
from apps.orders.models import Order
from common.response import success_response
from common.views import BaseModelViewSet

from .permissions import FinancePermission

# 收支流水类型：type → 中文名
LEDGER_TYPE_LABELS = {
    'income_receipt': '回款收入',
    'expense_factory': '工厂结算支出',
    'expense_logistics': '物流费用支出',
    'expense_service_fee': '服务费支出',
}

XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class PaymentInViewSet(BaseModelViewSet):
    """回款登记 CRUD + 收支流水聚合。

    数据范围：admin/finance 全量；salesman 看自己客户的订单数据；
    tracker 看派给自己的订单数据。写权限见 FinancePermission。
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

    # ---- 收支流水（纯聚合） ----

    @action(detail=False, methods=['get'], url_path='ledger')
    def ledger(self, request):
        rows = self._build_ledger_rows(request)
        return success_response(rows)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        rows = self._build_ledger_rows(request)

        wb = Workbook()
        ws = wb.active
        ws.title = '收支流水'
        ws.append(['日期', '类型', '金额', '币种', '说明'])
        for r in rows:
            ws.append([r['date'], LEDGER_TYPE_LABELS.get(r['type'], r['type']),
                       float(r['amount']), r['currency'], r['description']])

        resp = HttpResponse(
            content_type=XLSX_CONTENT_TYPE,
            headers={'Content-Disposition': 'attachment; filename=ledger.xlsx'},
        )
        wb.save(resp)
        return resp

    def _scope_queryset(self, qs, u, groups, prefix=''):
        """按角色过滤订单维度数据；无任何命中角色的账号返回空集，防止越权全量泄露。"""
        cond = Q()
        if 'salesman' in groups:
            cond |= Q(**{f'{prefix}customer__salesman': u})
        if 'tracker' in groups:
            cond |= Q(**{f'{prefix}tracker': u})
        return qs.filter(cond).distinct() if cond else qs.none()

    def _in_range(self, params, d):
        start, end = params.get('start_date'), params.get('end_date')
        s = str(d)
        if start and s < start:
            return False
        if end and s > end:
            return False
        return True

    def _build_ledger_rows(self, request):
        """聚合四类数据为统一流水：收入为正、支出为负，按日期倒序。"""
        u = request.user
        groups = set(u.groups.values_list('name', flat=True))
        scoped = not ('admin' in groups or 'finance' in groups)
        params = request.query_params
        want = lambda t: params.get('type') in (None, '', t)  # noqa: E731

        rows = []

        # 收入：回款登记
        if want('income_receipt'):
            qs = PaymentIn.objects.select_related('order', 'order__customer')
            if scoped:
                qs = self._scope_queryset(qs, u, groups, 'order__')
            for p in qs:
                if self._in_range(params, p.payment_date):
                    rows.append({
                        'type': 'income_receipt',
                        'date': str(p.payment_date),
                        'amount': p.amount_usd,
                        'currency': 'USD',
                        'description': f'回款 {p.order.order_no} 第{p.installment}期',
                        'source_id': p.id,
                    })

        # 支出：工厂付款记录
        if want('expense_factory'):
            qs = FactoryPaymentRecord.objects.select_related(
                'factory_payment', 'factory_payment__factory',
                'factory_payment__order_item', 'factory_payment__order_item__order',
                'factory_payment__order_item__order__customer',
            )
            if scoped:
                qs = self._scope_queryset(
                    qs, u, groups, 'factory_payment__order_item__order__'
                )
            for r in qs:
                if self._in_range(params, r.payment_date):
                    rows.append({
                        'type': 'expense_factory',
                        'date': str(r.payment_date),
                        'amount': -r.amount,
                        'currency': 'CNY',
                        'description': f'工厂结算 {r.factory_payment.factory.name}',
                        'source_id': r.id,
                    })

        # 支出：物流费用（以创建日计）
        if want('expense_logistics'):
            qs = Logistics.objects.select_related('order', 'order__customer')
            if scoped:
                qs = self._scope_queryset(qs, u, groups, 'order__')
            for l in qs:
                if l.cost <= 0:
                    continue
                d = l.created_at.date()
                if self._in_range(params, d):
                    rows.append({
                        'type': 'expense_logistics',
                        'date': str(d),
                        'amount': -l.cost,
                        'currency': l.cost_currency,
                        'description': f'物流发货 {l.order.order_no} #{l.seq}',
                        'source_id': l.id,
                    })

        # 支出：订单服务费（以下单日计；0 元跳过）
        if want('expense_service_fee'):
            qs = Order.objects.select_related('customer').filter(service_fee_usd__gt=0)
            if scoped:
                qs = self._scope_queryset(qs, u, groups)
            for o in qs:
                d = o.order_date or o.created_at.date()
                if self._in_range(params, d):
                    rows.append({
                        'type': 'expense_service_fee',
                        'date': str(d),
                        'amount': -o.service_fee_usd,
                        'currency': 'USD',
                        'description': f'服务费 {o.order_no}',
                        'source_id': o.id,
                    })

        rows.sort(key=lambda r: str(r['date']), reverse=True)
        return rows
