"""订单明细/删除的结算数据保护守卫（BUG-SIM-002）。

原则：结算单与付款记录是对账审计凭据——宁可拒绝，不可静默删除。
UI 编辑（serializer diff）与 Excel 导入共用本模块的校验规则。
"""
from decimal import Decimal

from rest_framework.exceptions import ValidationError

# 结算行冻结的金额字段（Q2:i）——结算单金额为建单快照，明细改价会造成口径分裂
AMOUNT_FIELDS = ('qty', 'unit_price', 'subtotal', 'cost_price')
FIELD_LABELS = {'qty': '数量', 'unit_price': '单价', 'subtotal': '金额小计', 'cost_price': '含税成本价'}


def _dec(v):
    return Decimal(str(v)) if v is not None else Decimal('0')


def _item_label(item):
    return item.product_no or item.model or f'序号{item.seq}'


def get_settled_item_ids(order):
    """订单内挂了结算单（不论未结/部分结/已结）的明细 id 集合。"""
    from apps.factory_payment.models import FactoryPayment
    return set(
        FactoryPayment.objects.filter(order_item__order=order).values_list('order_item_id', flat=True)
    )


def check_items_diff(order, incoming):
    """对 diff 更新作保护校验（Q1:A + Q2:i），失败汇总全部冲突行一次报出。

    incoming: payload 明细列表（dict，可含 id）。
    拦截两类操作：
    1. 删除已挂结算的明细（incoming 缺席该行）
    2. 修改已挂结算明细的金额字段
    """
    settled = get_settled_item_ids(order)
    if not settled:
        return
    existing = {it.id: it for it in order.items.all()}
    errors = []
    incoming_ids = []
    for p in incoming:
        iid = p.get('id')
        if not iid:
            continue
        incoming_ids.append(iid)
        cur = existing.get(iid)
        if cur is None or iid not in settled:
            continue
        for f in AMOUNT_FIELDS:
            if f in p and p[f] is not None and _dec(p[f]) != _dec(getattr(cur, f)):
                # 值为 None 视为未提交该字段，不参与冻结比较
                errors.append(
                    f'明细「{_item_label(cur)}」已挂结算单，{FIELD_LABELS[f]}等金额字段已冻结，'
                    f'如需调整请先由管理员删除该结算单')
                break
    for iid, cur in existing.items():
        if iid not in incoming_ids and iid in settled:
            errors.append(
                f'明细「{_item_label(cur)}」已挂结算单，不可删除；'
                f'如需删除请先由管理员删除该结算单')
    if errors:
        raise ValidationError('；'.join(errors))


def ensure_order_deletable(order):
    """挂有结算单（含其下付款记录）的订单禁止删除（Q5:i）。

    单条删除走 perform_destroy；批量删除由 ViewSet.validate_bulk_delete 转为 forbidden 清单。
    """
    from apps.factory_payment.models import FactoryPayment
    if FactoryPayment.objects.filter(order_item__order=order).exists():
        raise ValidationError('订单已挂结算单/付款记录，禁止删除；如需删除请先由管理员删除该结算单')
