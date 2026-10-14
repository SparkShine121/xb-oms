// BUG-SIM-026 Q3:a：模型英文名 → 中文标签（操作日志/审批列表共用；后端存英文名）
export const MODEL_NAME_LABELS: Record<string, string> = {
  Order: '订单',
  OrderItem: '订单明细',
  FactoryPayment: '工厂结算',
  FactoryPaymentRecord: '工厂付款',
  PaymentIn: '回款',
  TrackingLog: '跟单日志',
  Logistics: '物流发货',
  User: '用户',
  Customer: '客户',
  Product: '产品',
  Factory: '工厂',
  Category: '类目',
  LogisticsProvider: '物流服务商',
  ExchangeRate: '汇率',
  ApprovalRequest: '审批申请',
  OperationLog: '操作日志',
  BackupRecord: '备份记录',
}

export function modelLabel(name?: string | null): string {
  if (!name) return '—'
  return MODEL_NAME_LABELS[name] ?? name
}
