import io
import openpyxl
from decimal import Decimal
from django.db import transaction
from .models import Order, OrderItem, ExchangeRate, calc_order_profit
from .services import get_settled_item_ids
from apps.basic_info.models import Customer, Product, Factory

ALI_STATUS_MAP = {
    '待确认': '接单', '待发货': '排产', '已发货': '发货', '交易成功': '签收',
    '交易失败': '已取消', '已退款': '已取消',
}
CANCELLED_STATUSES = {'交易失败', '已退款'}

ORDER_COLUMNS = [
    '订单状态', '产品清单', '订单日期', '联系人', '订单名称', '运费', '物流保险费', '附加费用',
    '订单金额（USD）', '交易服务费(USD)', '运输成本', '承运商', '物流', '单号', '备注',
]
ITEM_COLUMNS = [
    '序号', '供应商', '数量', '型号', '产品规格', '单价', '金额小计', '含税成本价',
    '产品毛利', '毛利润率', '产品编号',
]


def _match_customer(name):
    if not name:
        return None
    name = str(name).strip()
    c = Customer.objects.filter(name=name).first()
    if c:
        return c
    c = Customer.objects.filter(name__iexact=name).first()
    return c


def _match_factory(name):
    if not name:
        return None
    name = str(name).strip()
    f = Factory.objects.filter(name=name).first()
    if f:
        return f
    f = Factory.objects.filter(alias=name).first()
    return f


def _match_product(no):
    if not no:
        return None
    return Product.objects.filter(product_no=str(no).strip()).first()


def _dec(v):
    return Decimal(str(v)) if v is not None else Decimal('0')


def _in_data_scope(order, user):
    """BUG-SIM-002 Q7:i：导入更新已存在订单需在操作者数据范围内。

    admin/finance 全部；salesman 自己客户的订单；tracker 派给自己的订单。
    user=None（脚本/旧调用）不校验。
    """
    if user is None or user.is_superuser:
        return True
    groups = set(user.groups.values_list('name', flat=True))
    if 'admin' in groups or 'finance' in groups:
        return True
    if 'salesman' in groups and order.customer and order.customer.salesman_id == user.id:
        return True
    if 'tracker' in groups and order.tracker_id == user.id:
        return True
    return False


def _match_item_refs(it, d, unmatched):
    product = _match_product(it['product_no'])
    if it['product_no'] and not product:
        unmatched['products'].append({'row': d['row'], 'product_no': str(it['product_no'])})
    factory = _match_factory(it['supplier'])
    if it['supplier'] and not factory:
        unmatched['factories'].append({'row': d['row'], 'name': str(it['supplier'])})
    return product, factory


def _create_items(order, d, unmatched):
    """新建订单：按 Excel 行建明细（行为与历史版本一致）。"""
    for it in d['items']:
        product, factory = _match_item_refs(it, d, unmatched)
        OrderItem.objects.create(
            order=order, seq=it['seq'] or 0, product=product, factory=factory,
            model=it['model'] or '', product_no=str(it['product_no'] or ''), spec=it['spec'] or '',
            qty=it['qty'] or 0, unit_price=it['price'] or 0, subtotal=it['subtotal'] or 0,
            cost_price=it['cost'] or 0,
        )


def _update_items(order, d, unmatched):
    """更新已存在订单：不再整组替换（BUG-SIM-002）。

    按 product_no 匹配（Q6:b）：命中唯一明细 → 原位更新（行 id 不变，结算保持）；
    未命中 → 新建；已有明细在 Excel 缺席 → 删除（挂结算则拒绝）。
    结算行金额字段冻结（Q2:i）。product_no 重复/为空 → 整单失败（宁可拒绝不可错账）。
    """
    excel_nos = [str(it['product_no'] or '').strip() for it in d['items']]
    if any(not n for n in excel_nos):
        raise ValueError('更新已存在订单时明细行产品编号不能为空，请走编辑页修改')
    if len(set(excel_nos)) != len(excel_nos):
        raise ValueError('同一订单内产品编号重复，无法安全更新，请走编辑页修改')
    existing = list(order.items.all())
    by_no = {}
    for cur in existing:
        if not cur.product_no:
            # 空 product_no 永远无法匹配，重导会被误判为"Excel 缺席"而静默删除
            raise ValueError('已有明细存在产品编号为空的行，无法安全更新，请走编辑页修改')
        if cur.product_no in by_no:
            raise ValueError('已有明细产品编号重复，无法安全更新，请走编辑页修改')
        by_no[cur.product_no] = cur
    settled = get_settled_item_ids(order)
    kept = set()
    for it, no in zip(d['items'], excel_nos):
        product, factory = _match_item_refs(it, d, unmatched)
        cur = by_no.get(no)
        if cur is not None:
            kept.add(cur.id)
            if cur.id in settled:
                # 冻结校验：任一金额字段与现值不符 → 拒绝整单
                for f_excel, f_model in (('qty', 'qty'), ('price', 'unit_price'),
                                         ('subtotal', 'subtotal'), ('cost', 'cost_price')):
                    if _dec(it[f_excel]) != _dec(getattr(cur, f_model)):
                        raise ValueError(
                            f'明细「{no}」已挂结算单，金额字段冻结，如需调整请先由管理员删除该结算单')
            cur.seq = it['seq'] or 0
            cur.product = product
            cur.factory = factory
            cur.model = it['model'] or ''
            cur.spec = it['spec'] or ''
            if cur.id not in settled:
                cur.qty = it['qty'] or 0
                cur.unit_price = it['price'] or 0
                cur.subtotal = it['subtotal'] or 0
                cur.cost_price = it['cost'] or 0
            cur.save()
        else:
            OrderItem.objects.create(
                order=order, seq=it['seq'] or 0, product=product, factory=factory,
                model=it['model'] or '', product_no=no, spec=it['spec'] or '',
                qty=it['qty'] or 0, unit_price=it['price'] or 0, subtotal=it['subtotal'] or 0,
                cost_price=it['cost'] or 0,
            )
    for cur in existing:
        if cur.id not in kept:
            if cur.id in settled:
                raise ValueError(
                    f'明细「{cur.product_no}」已挂结算单，不可删除；如需删除请先由管理员删除该结算单')
            cur.delete()


def import_orders(file, user=None):
    """导入订单 Excel。user 为操作者（视图层传入），用于更新路径的归属校验。"""
    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(headers) if h}
    success, failures = 0, []
    created_order_nos = []  # 新建（非更新）的订单号，供视图层挂审批
    unmatched = {'customers': [], 'products': [], 'factories': []}
    # 按 order_no 分组（主表字段可能合并单元格，从每行读但按订单号去重）
    orders_data = {}
    order_row_map = {}
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        order_no = row[col['订单名称']] if '订单名称' in col else None
        if not order_no:
            failures.append({'row': row_idx, 'reason': '订单号为空'})
            continue
        order_no = str(order_no).strip()
        if order_no not in orders_data:
            orders_data[order_no] = {
                'ali_status': row[col['订单状态']] if '订单状态' in col else '',
                'order_date': row[col['订单日期']] if '订单日期' in col else None,
                'contact': row[col['联系人']] if '联系人' in col else '',
                'freight': row[col['运费']] if '运费' in col else 0,
                'insurance': row[col['物流保险费']] if '物流保险费' in col else 0,
                'surcharge': row[col['附加费用']] if '附加费用' in col else 0,
                'amount': row[col['订单金额（USD）']] if '订单金额（USD）' in col else 0,
                'service_fee': row[col['交易服务费(USD)']] if '交易服务费(USD)' in col else 0,
                'transport': row[col['运输成本']] if '运输成本' in col else 0,
                'carrier': row[col['承运商']] if '承运商' in col else '',
                'logistics': row[col['物流']] if '物流' in col else '',
                'tracking_no': row[col['单号']] if '单号' in col else '',
                'remark': row[col['备注']] if '备注' in col else '',
                'row': row_idx,
                'items': [],
            }
            order_row_map[order_no] = row_idx
        # 产品行
        item = {
            'seq': row[col['序号']] if '序号' in col else 0,
            'supplier': row[col['供应商']] if '供应商' in col else '',
            'qty': row[col['数量']] if '数量' in col else 0,
            'model': row[col['型号']] if '型号' in col else '',
            'spec': row[col['产品规格']] if '产品规格' in col else '',
            'price': row[col['单价']] if '单价' in col else 0,
            'subtotal': row[col['金额小计']] if '金额小计' in col else 0,
            'cost': row[col['含税成本价']] if '含税成本价' in col else 0,
            'product_no': row[col['产品编号']] if '产品编号' in col else '',
        }
        orders_data[order_no]['items'].append(item)

    for order_no, d in orders_data.items():
        try:
            # 每订单原子化：任一校验失败 → 该订单全部写入回滚，只进 failures 清单
            with transaction.atomic():
                customer = _match_customer(d['contact'])
                if d['contact'] and not customer:
                    unmatched['customers'].append({'row': d['row'], 'name': str(d['contact'])})
                ali_status = str(d['ali_status'] or '').strip()
                tracking_status = ALI_STATUS_MAP.get(ali_status, '')
                is_cancelled = ali_status in CANCELLED_STATUSES
                order, created = Order.objects.update_or_create(
                    order_no=order_no,
                    defaults={
                        'ali_status': ali_status, 'tracking_status': tracking_status, 'is_cancelled': is_cancelled,
                        'order_date': d['order_date'],
                        'customer': customer,
                        'salesman': customer.salesman if customer else None,
                        'amount_usd': d['amount'] or 0, 'freight': d['freight'] or 0, 'insurance': d['insurance'] or 0,
                        'surcharge': d['surcharge'] or 0, 'service_fee_usd': d['service_fee'] or 0,
                        'transport_cost': d['transport'] or 0, 'carrier': d['carrier'] or '',
                        'logistics_method': d['logistics'] or '',
                        'tracking_no': d['tracking_no'] or '', 'remark': d['remark'] or '',
                    },
                )
                if created:
                    created_order_nos.append(order_no)
                else:
                    # BUG-SIM-002 Q7:i：更新路径校验操作者数据范围
                    if not _in_data_scope(order, user):
                        raise ValueError('无权限更新该订单（数据范围外）')
                # tracker：新订单填 customer.tracker；已存在若空才填
                if not order.tracker and customer and customer.tracker:
                    order.tracker = customer.tracker
                    order.save(update_fields=['tracker'])
                if created:
                    _create_items(order, d, unmatched)
                else:
                    _update_items(order, d, unmatched)
                calc_order_profit(order)
                success += 1
        except Exception as e:
            failures.append({'row': d['row'], 'reason': str(e)})
    return {'success_count': success, 'fail_count': len(failures), 'failures': failures,
            'unmatched': unmatched, 'created_order_nos': created_order_nos}


def build_order_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(ORDER_COLUMNS + ITEM_COLUMNS)
    ws.append([
        '待确认', '', '2026-05-12', '吴芳', '示例订单', 100, 10, 5, 1000, 30, 50,
        '圆通', 'EMS', 'T1', '', '1', '华鑫', 10, 'M1', '尺寸:54*35',
        '100', '1000', '720', '', '', 'P001',
    ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf