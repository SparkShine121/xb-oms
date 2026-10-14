import type { Component } from 'vue'
import {
  PhChartBar, PhFolderOpen, PhHandCoins, PhListChecks, PhReceipt, PhShieldCheck, PhTruck, PhWallet,
} from '@phosphor-icons/vue'

export interface MenuChild {
  path: string
  label: string
}

export interface MenuGroup {
  key: string
  label: string
  icon: Component
  /** 仅 admin 可见（现系统管理分组的显隐语义） */
  adminOnly?: boolean
  children: MenuChild[]
  /** 平铺单页项（如数据分析）的直达路由；children 非空时不用 */
  path?: string
}

export const MENU_GROUPS: MenuGroup[] = [
  {
    key: 'basic-info', label: '基础信息', icon: PhFolderOpen,
    children: [
      { path: '/basic-info/category', label: '类目' },
      { path: '/basic-info/product', label: '产品库' },
      { path: '/basic-info/factory', label: '工厂库' },
      { path: '/basic-info/logistics', label: '物流服务商' },
      { path: '/basic-info/customer', label: '客户' },
      { path: '/basic-info/rates', label: '汇率' },
    ],
  },
  {
    key: 'system', label: '系统管理', icon: PhShieldCheck, adminOnly: true,
    children: [
      { path: '/system/approvals', label: '待审批' },
      { path: '/system/users', label: '用户管理' },
      { path: '/system/logs', label: '操作日志' },
      { path: '/system/backups', label: '备份管理' },
    ],
  },
  { key: 'orders', label: '订单管理', icon: PhReceipt, children: [{ path: '/orders/list', label: '订单列表' }] },
  { key: 'tracking', label: '跟单管理', icon: PhListChecks, children: [{ path: '/tracking', label: '跟单工作台' }] },
  {
    key: 'factory-payment', label: '工厂结算', icon: PhHandCoins,
    children: [
      { path: '/factory-payment', label: '结算单' },
      { path: '/factory-payment/statement', label: '对账单' },
    ],
  },
  { key: 'logistics', label: '物流管理', icon: PhTruck, children: [{ path: '/logistics', label: '发货单' }] },
  { key: 'finance', label: '轻财务', icon: PhWallet, children: [{ path: '/finance', label: '收支流水' }] },
  { key: 'analytics', label: '数据分析', icon: PhChartBar, children: [], path: '/analytics' },
]

/** 路由 → 所属分组（前缀匹配；/analytics 精确匹配） */
export function groupOfPath(path: string): MenuGroup | undefined {
  return MENU_GROUPS.find((g) => {
    if (g.children.length === 0) return g.path === path
    return g.children.some((c) => path === c.path || path.startsWith(c.path + '/')) || path.startsWith('/' + g.key)
  })
}
