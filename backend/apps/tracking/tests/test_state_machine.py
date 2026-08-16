from apps.tracking.state_machine import next_node, prev_node, TRACKING_FLOW

def test_flow_order():
    assert TRACKING_FLOW == ['接单','排产','生产中','质检','发货','签收','结算','回款']

def test_next_node():
    assert next_node('接单') == '排产'
    assert next_node('排产') == '生产中'
    assert next_node('回款') is None  # 终态

def test_prev_node():
    assert prev_node('排产') == '接单'
    assert prev_node('接单') is None  # 起点无上一
    assert prev_node('回款') == '结算'

def test_unknown_node():
    assert next_node('未知') is None
    assert prev_node('未知') is None
