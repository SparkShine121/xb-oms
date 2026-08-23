"""数据分析聚合 API（Task 5）。

不建业务表，纯聚合查询：
- sales           销售结算表：按业务员聚合 + 月度趋势
- factory-summary 工厂账单汇总：应付/已付/未付
- tracking-summary 跟单信息汇总：节点分布 + 各节点平均停留时长
- overview        年度总览：总额 + 月度销售额/毛利趋势
"""

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView

from common.response import success_response
from apps.analytics.permissions import AnalyticsPermission
from apps.orders.models import Order
from apps.factory_payment.models import FactoryPayment
from apps.tracking.models import TrackingLog


def _f(v):
    """Decimal/None → float，便于 JSON 序列化与前端运算。"""
    return float(v) if v is not None else 0.0


class SalesSummaryView(APIView):
    """销售结算表：按业务员/客户聚合 + 按月趋势。

    筛选：?year=2026  ?salesman=<user_id>  ?customer=<customer_id>
    """
    permission_classes = [AnalyticsPermission]

    def get(self, request):
        qs = Order.objects.filter(is_cancelled=False)
        year = request.query_params.get('year')
        if year:
            qs = qs.filter(order_date__year=year)
        salesman = request.query_params.get('salesman')
        if salesman:
            qs = qs.filter(salesman_id=salesman)
        customer = request.query_params.get('customer')
        if customer:
            qs = qs.filter(customer_id=customer)

        by_salesman = self._group(qs, 'salesman__username')
        by_customer = self._group(qs, 'customer__name')

        monthly = {}
        for o in qs:
            m = o.order_date.strftime('%Y-%m') if o.order_date else 'unknown'
            d = monthly.setdefault(m, {'month': m, 'count': 0, 'sales': 0.0, 'profit': 0.0})
            d['count'] += 1
            d['sales'] += _f(o.amount_usd)
            d['profit'] += _f(o.order_profit_usd)
        monthly_list = sorted(monthly.values(), key=lambda x: x['month'])

        return success_response({
            'by_salesman': by_salesman,
            'by_customer': by_customer,
            'monthly': monthly_list,
        })

    @staticmethod
    def _group(qs, dim):
        """按维度聚合：订单数/总金额/总毛利/毛利率，按销售额降序。"""
        rows = qs.values(dim).annotate(
            order_count=Count('id'),
            total_amount=Sum('amount_usd'),
            total_profit=Sum('order_profit_usd'),
        ).order_by('-total_amount')
        data = []
        for r in rows:
            amount = _f(r['total_amount'])
            profit = _f(r['total_profit'])
            data.append({
                dim: r[dim] or '未分配',
                'order_count': r['order_count'],
                'total_amount': round(amount, 2),
                'total_profit': round(profit, 2),
                'profit_rate': round(profit / amount, 4) if amount else 0,
            })
        return data


class FactorySummaryView(APIView):
    """工厂账单汇总：按工厂聚合应付/已付/未付。

    筛选：?year=2026  ?factory=<factory_id>
    """
    permission_classes = [AnalyticsPermission]

    def get(self, request):
        qs = FactoryPayment.objects.all()
        year = request.query_params.get('year')
        if year:
            qs = qs.filter(created_at__year=year)
        factory_id = request.query_params.get('factory')
        if factory_id:
            qs = qs.filter(factory_id=factory_id)

        rows = qs.values('factory__name').annotate(
            total_amount=Sum('amount_cny'),
            total_paid=Sum('paid_amount'),
            payment_count=Count('id'),
        ).order_by('-total_amount')

        data = []
        for r in rows:
            amount = _f(r['total_amount'])
            paid = _f(r['total_paid'])
            data.append({
                'factory__name': r['factory__name'] or '未知工厂',
                'total_amount': round(amount, 2),
                'total_paid': round(paid, 2),
                'total_unpaid': round(amount - paid, 2),
                'payment_count': r['payment_count'],
            })
        return success_response(data)


class TrackingSummaryView(APIView):
    """跟单信息汇总：各节点分布 + 各节点平均停留时长。

    停留时长 = 同一订单相邻两条跟单日志的时间差，按前一节点归属求平均。
    筛选：?year=2026（按订单下单日期过滤）
    """
    permission_classes = [AnalyticsPermission]

    def get(self, request):
        order_filters = {'is_cancelled': False}
        year = request.query_params.get('year')
        if year:
            order_filters['order_date__year'] = year

        qs = Order.objects.exclude(tracking_status='').filter(**order_filters)

        node_distribution = [
            {'node': r['tracking_status'], 'count': r['count']}
            for r in qs.values('tracking_status').annotate(
                count=Count('id')).order_by('-count')
        ]

        # 平均停留时长：遍历范围内订单的日志时间线，相邻差值归前节点
        # （日志按订单年份/取消状态同步过滤，与节点分布口径一致）
        log_filters = {f'order__{k}': v for k, v in order_filters.items()}
        logs = list(TrackingLog.objects.filter(**log_filters).order_by('order_id', 'created_at', 'id'))
        dwell = {}  # node -> [总秒数, 次数]
        prev = None
        for log in logs:
            if prev is not None and prev.order_id == log.order_id and prev.node != log.node:
                delta = (log.created_at - prev.created_at).total_seconds()
                if delta >= 0:
                    acc = dwell.setdefault(prev.node, [0.0, 0])
                    acc[0] += delta
                    acc[1] += 1
            prev = log
        avg_dwell_days = [
            {'node': node, 'avg_days': round(total / cnt / 86400, 2)}
            for node, (total, cnt) in sorted(dwell.items(), key=lambda kv: -kv[1][1])
        ]

        return success_response({
            'node_distribution': node_distribution,
            'avg_dwell_days': avg_dwell_days,
        })


class OverviewView(APIView):
    """管理人员报表总览：总额卡片 + 月度销售额/毛利趋势。

    筛选：?year=2026
    """
    permission_classes = [AnalyticsPermission]

    def get(self, request):
        orders = Order.objects.filter(is_cancelled=False)
        year = request.query_params.get('year')
        if year:
            orders = orders.filter(order_date__year=year)

        agg = orders.aggregate(total_sales=Sum('amount_usd'), total_profit=Sum('order_profit_usd'))

        monthly_rows = (
            orders.exclude(order_date__isnull=True)
            .annotate(month=TruncMonth('order_date'))
            .values('month')
            .annotate(sales=Sum('amount_usd'), profit=Sum('order_profit_usd'))
            .order_by('month')
        )
        monthly = [
            {
                'month': r['month'].strftime('%Y-%m'),
                'sales': round(_f(r['sales']), 2),
                'profit': round(_f(r['profit']), 2),
            }
            for r in monthly_rows
        ]

        return success_response({
            'total_orders': orders.count(),
            'total_sales': round(_f(agg['total_sales']), 2),
            'total_profit': round(_f(agg['total_profit']), 2),
            'monthly': monthly,
        })
