TRACKING_FLOW = ['接单','排产','生产中','质检','发货','签收','结算','回款']

def next_node(node):
    if node not in TRACKING_FLOW:
        return None
    i = TRACKING_FLOW.index(node)
    return TRACKING_FLOW[i+1] if i < len(TRACKING_FLOW)-1 else None

def prev_node(node):
    if node not in TRACKING_FLOW:
        return None
    i = TRACKING_FLOW.index(node)
    return TRACKING_FLOW[i-1] if i > 0 else None
