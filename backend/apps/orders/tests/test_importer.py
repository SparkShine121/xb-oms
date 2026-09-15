import pytest
from io import BytesIO
import openpyxl
from apps.orders.importers import import_orders, build_order_template, ALI_STATUS_MAP
from apps.orders.models import Order
from apps.basic_info.models import Customer, Product, Factory, Category
from datetime import date


@pytest.fixture
def rate(db):
    from apps.orders.models import ExchangeRate
    return ExchangeRate.objects.create(currency_pair='USD/CNY', rate='7.20', effective_date=date(2026, 1, 1))


def make_xlsx(records):
    # records: list of dict {订单级字段 + items:[产品行字段]}
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = [
        '订单状态', '产品清单', '订单日期', '联系人', '订单名称', '运费', '物流保险费', '附加费用',
        '订单金额（USD）', '交易服务费(USD)', '运输成本', '承运商', '物流', '单号', '备注',
        '序号', '供应商', '数量', '型号', '产品规格', '单价', '金额小计', '含税成本价',
        '产品毛利', '毛利润率', '产品编号',
    ]
    ws.append(headers)
    for rec in records:
        for i, it in enumerate(rec['items']):
            row = [
                rec['ali_status'], '', rec['order_date'], rec['contact'], rec['order_no'],
                rec['freight'], rec['insurance'], rec['surcharge'], rec['amount'],
                rec['service_fee'], rec['transport'], rec['carrier'], rec['logistics'],
                rec['tracking_no'], rec['remark'],
                it['seq'], it['supplier'], it['qty'], it['model'], it['spec'],
                it['price'], it['subtotal'], it['cost'], it.get('profit', ''),
                it.get('profit_rate', ''), it['product_no'],
            ]
            ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_import_creates_orders(db, rate):
    Customer.objects.create(name='吴芳')
    buf = make_xlsx([{
        'ali_status': '待确认', 'order_date': '2026-05-12', 'contact': '吴芳', 'order_no': 'O1',
        'freight': 100, 'insurance': 10, 'surcharge': 5, 'amount': 1000, 'service_fee': 30,
        'transport': 50, 'carrier': '圆通', 'logistics': 'EMS', 'tracking_no': 'T1', 'remark': '',
        'items': [{'seq': 1, 'supplier': '华鑫', 'qty': 10, 'model': 'M1', 'spec': 'S',
                    'price': 100, 'subtotal': 1000, 'cost': 720, 'product_no': 'P1'}],
    }])
    r = import_orders(buf)
    assert r['success_count'] == 1 and r['fail_count'] == 0
    o = Order.objects.get(order_no='O1')
    assert o.tracking_status == '接单' and o.is_cancelled is False
    assert o.items.count() == 1
    # customer 关联
    assert o.customer is not None and o.customer.name == '吴芳'


def test_import_cancelled_status(db, rate):
    buf = make_xlsx([{
        'ali_status': '交易失败', 'order_date': '2026-05-12', 'contact': 'X', 'order_no': 'O2',
        'freight': 0, 'insurance': 0, 'surcharge': 0, 'amount': 0, 'service_fee': 0,
        'transport': 0, 'carrier': '', 'logistics': '', 'tracking_no': '', 'remark': '',
        'items': [{'seq': 1, 'supplier': '', 'qty': 1, 'model': '', 'spec': '',
                    'price': 0, 'subtotal': 0, 'cost': 0, 'product_no': ''}],
    }])
    import_orders(buf)
    o = Order.objects.get(order_no='O2')
    assert o.is_cancelled is True and o.tracking_status == '已取消'


def test_import_upsert_replaces_items(db, rate):
    Customer.objects.create(name='吴芳')
    buf1 = make_xlsx([{
        'ali_status': '待确认', 'order_date': '2026-05-12', 'contact': '吴芳', 'order_no': 'O1',
        'freight': 0, 'insurance': 0, 'surcharge': 0, 'amount': 100, 'service_fee': 0,
        'transport': 0, 'carrier': '', 'logistics': '', 'tracking_no': '', 'remark': '',
        'items': [{'seq': 1, 'supplier': '', 'qty': 1, 'model': '', 'spec': '',
                    'price': 100, 'subtotal': 100, 'cost': 72, 'product_no': 'P1'}],
    }])
    import_orders(buf1)
    buf2 = make_xlsx([{
        'ali_status': '待发货', 'order_date': '2026-05-12', 'contact': '吴芳', 'order_no': 'O1',
        'freight': 0, 'insurance': 0, 'surcharge': 0, 'amount': 200, 'service_fee': 0,
        'transport': 0, 'carrier': '', 'logistics': '', 'tracking_no': '', 'remark': '',
        'items': [
            {'seq': 1, 'supplier': '', 'qty': 2, 'model': '', 'spec': '',
             'price': 100, 'subtotal': 200, 'cost': 72, 'product_no': 'P1'},
            {'seq': 2, 'supplier': '', 'qty': 1, 'model': '', 'spec': '',
             'price': 50, 'subtotal': 50, 'cost': 36, 'product_no': 'P2'},
        ],
    }])
    r = import_orders(buf2)
    o = Order.objects.get(order_no='O1')
    assert o.tracking_status == '排产' and str(o.amount_usd) == '200.00'
    assert o.items.count() == 2  # 整组替换


def test_import_unmatched(db, rate):
    buf = make_xlsx([{
        'ali_status': '待确认', 'order_date': '2026-05-12', 'contact': '新客户', 'order_no': 'O3',
        'freight': 0, 'insurance': 0, 'surcharge': 0, 'amount': 100, 'service_fee': 0,
        'transport': 0, 'carrier': '', 'logistics': '', 'tracking_no': '', 'remark': '',
        'items': [{'seq': 1, 'supplier': '新工厂', 'qty': 1, 'model': '', 'spec': '',
                    'price': 100, 'subtotal': 100, 'cost': 72, 'product_no': 'NEWP'}],
    }])
    r = import_orders(buf)
    o = Order.objects.get(order_no='O3')
    assert o.customer is None  # 未匹配
    assert any(u['name'] == '新客户' for u in r['unmatched']['customers'])
    assert any(u['name'] == '新工厂' for u in r['unmatched']['factories'])


def test_import_tracker_auto(db, rate):
    from django.contrib.auth.models import User
    t = User.objects.create_user('tracker1', password='pw123456')
    Customer.objects.create(name='吴芳', tracker=t)
    buf = make_xlsx([{
        'ali_status': '待确认', 'order_date': '2026-05-12', 'contact': '吴芳', 'order_no': 'O1',
        'freight': 0, 'insurance': 0, 'surcharge': 0, 'amount': 100, 'service_fee': 0,
        'transport': 0, 'carrier': '', 'logistics': '', 'tracking_no': '', 'remark': '',
        'items': [{'seq': 1, 'supplier': '', 'qty': 1, 'model': '', 'spec': '',
                    'price': 100, 'subtotal': 100, 'cost': 72, 'product_no': ''}],
    }])
    import_orders(buf)
    assert Order.objects.get(order_no='O1').tracker == t


def test_import_template_download(db):
    buf = build_order_template()
    wb = openpyxl.load_workbook(buf)
    assert wb.active.max_row >= 2  # 表头+示例


def test_import_bad_file(db):
    with pytest.raises(Exception):
        import_orders(BytesIO(b'not an xlsx'))
# ---- BUG-SIM-002: 导入 diff 更新 + 结算数据保护 + 归属校验（Q7:i）----
from django.contrib.auth.models import User, Group
from apps.factory_payment.models import FactoryPayment
from apps.orders.models import OrderItem

BASE_REC = {
    'ali_status': '待确认', 'order_date': '2026-05-12', 'contact': '吴芳', 'order_no': 'O1',
    'freight': 100, 'insurance': 10, 'surcharge': 5, 'amount': 1000, 'service_fee': 30,
    'transport': 50, 'carrier': '圆通', 'logistics': 'EMS', 'tracking_no': 'T1', 'remark': '',
}


def _item(seq, product_no, qty=10, price=100, subtotal=1000, cost=720, spec='S', supplier='华鑫'):
    return {'seq': seq, 'supplier': supplier, 'qty': qty, 'model': 'M1', 'spec': spec,
            'price': price, 'subtotal': subtotal, 'cost': cost, 'product_no': product_no}


def _settled_import_setup():
    """首导 O1（P1、P2 两行），给 P2 挂结算单；返回 (order, item_p1, item_p2, fp)"""
    Customer.objects.create(name='吴芳')
    f = Factory.objects.create(name='华鑫')
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1'), _item(2, 'P2')]}])
    r = import_orders(buf)
    assert r['success_count'] == 1, r['failures']
    o = Order.objects.get(order_no='O1')
    ip1 = o.items.get(product_no='P1')
    ip2 = o.items.get(product_no='P2')
    fp = FactoryPayment.objects.create(order_item=ip2, factory=f, amount_cny='720.00')
    return o, ip1, ip2, fp


def test_reimport_keeps_settlement(db, rate):
    """原样重导（P1 改规格，P2 原样）→ 行 id 不变，结算+付款记录完好"""
    o, ip1, ip2, fp = _settled_import_setup()
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1', spec='改规格'), _item(2, 'P2')]}])
    r = import_orders(buf)
    assert r['success_count'] == 1 and r['fail_count'] == 0, r['failures']
    assert o.items.count() == 2
    assert list(o.items.values_list('id', flat=True).order_by('id')) == sorted([ip1.id, ip2.id])
    ip1.refresh_from_db()
    assert ip1.spec == '改规格'
    fp.refresh_from_db()
    assert fp.order_item_id == ip2.id  # 结算仍挂原行


def test_reimport_missing_settled_row_fails(db, rate):
    o, ip1, ip2, fp = _settled_import_setup()
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1')]}])  # Excel 缺 P2（已挂结算）
    r = import_orders(buf)
    assert r['success_count'] == 0 and r['fail_count'] == 1
    assert '已挂结算' in r['failures'][0]['reason']
    assert OrderItem.objects.filter(id=ip2.id).exists()
    assert FactoryPayment.objects.filter(id=fp.id).exists()


def test_reimport_amount_change_on_settled_row_fails(db, rate):
    o, ip1, ip2, fp = _settled_import_setup()
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1'), _item(2, 'P2', subtotal=1200, cost=864)]}])
    r = import_orders(buf)
    assert r['success_count'] == 0 and r['fail_count'] == 1
    assert '冻结' in r['failures'][0]['reason']
    ip2.refresh_from_db()
    assert str(ip2.subtotal) == '1000.00'
    assert FactoryPayment.objects.filter(id=fp.id).exists()


def test_reimport_out_of_scope_salesman_fails(db, rate):
    """Q7:i 归属校验：非本人客户的订单不可通过导入更新"""
    owner = User.objects.create_user('owner', password='pw123456')
    owner.groups.add(Group.objects.get(name='salesman'))
    Customer.objects.create(name='吴芳', salesman=owner)  # 重置归属再首导
    Order.objects.all().delete()
    FactoryPayment.objects.all().delete()
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1')]}])
    r = import_orders(buf, user=owner)
    assert r['success_count'] == 1, r['failures']

    other = User.objects.create_user('other_sales', password='pw123456')
    other.groups.add(Group.objects.get(name='salesman'))
    buf2 = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1', spec='越权改')]}])
    r2 = import_orders(buf2, user=other)
    assert r2['success_count'] == 0 and r2['fail_count'] == 1
    assert '无权限更新该订单' in r2['failures'][0]['reason']
    o = Order.objects.get(order_no='O1')
    assert o.items.get(product_no='P1').spec == 'S'  # 未被越权修改


def test_reimport_duplicate_product_no_fails(db, rate):
    """安全失败规则：同订单 Excel 内 product_no 重复 → 整单失败，不猜匹配"""
    Customer.objects.create(name='吴芳')
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1'), _item(2, 'P1')]}])
    r = import_orders(buf)  # 新建路径容忍（现状），先建成
    assert r['success_count'] == 1
    buf2 = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1'), _item(2, 'P1')]}])
    r2 = import_orders(buf2)  # 更新路径：重复键 → 拒绝
    assert r2['success_count'] == 0 and r2['fail_count'] == 1
    assert '重复' in r2['failures'][0]['reason']


def test_reimport_blank_product_no_fails_on_update(db, rate):
    """安全失败规则：更新已有订单时 Excel 行缺产品编号 → 整单失败"""
    Customer.objects.create(name='吴芳')
    buf = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1')]}])
    assert import_orders(buf)['success_count'] == 1
    buf2 = make_xlsx([{**BASE_REC, 'items': [_item(1, 'P1'), _item(2, '')]}])
    r2 = import_orders(buf2)
    assert r2['success_count'] == 0 and r2['fail_count'] == 1
    assert '产品编号' in r2['failures'][0]['reason']
