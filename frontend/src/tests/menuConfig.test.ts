// @vitest-environment node
// 菜单结构不变量：menuConfig 必须与旧 MainLayout 的 el-menu 逐项一致（标签零改动的锁）
import { describe, expect, it } from 'vitest'
import { MENU_GROUPS, groupOfPath } from '../layouts/menuConfig'

describe('menuConfig 结构不变量', () => {
  it('分组顺序与标签与旧菜单一致', () => {
    expect(MENU_GROUPS.map((g) => g.label)).toEqual([
      '基础信息', '系统管理', '订单管理', '跟单管理', '工厂结算', '物流管理', '轻财务', '数据分析',
    ])
  })

  it('子项标签与路由逐项一致', () => {
    expect(MENU_GROUPS[0].children).toEqual([
      { path: '/basic-info/category', label: '类目' },
      { path: '/basic-info/product', label: '产品库' },
      { path: '/basic-info/factory', label: '工厂库' },
      { path: '/basic-info/logistics', label: '物流服务商' },
      { path: '/basic-info/customer', label: '客户' },
    ])
    expect(MENU_GROUPS[1].children).toEqual([
      { path: '/system/approvals', label: '待审批' },
      { path: '/system/users', label: '用户管理' },
      { path: '/system/logs', label: '操作日志' },
      { path: '/system/backups', label: '备份管理' },
    ])
    expect(MENU_GROUPS[2].children).toEqual([{ path: '/orders/list', label: '订单列表' }])
    expect(MENU_GROUPS[3].children).toEqual([{ path: '/tracking', label: '跟单工作台' }])
    expect(MENU_GROUPS[4].children).toEqual([
      { path: '/factory-payment', label: '结算单' },
      { path: '/factory-payment/statement', label: '对账单' },
    ])
    expect(MENU_GROUPS[5].children).toEqual([{ path: '/logistics', label: '发货单' }])
    expect(MENU_GROUPS[6].children).toEqual([{ path: '/finance', label: '收支流水' }])
  })

  it('权限与平铺项', () => {
    expect(MENU_GROUPS[1].adminOnly).toBe(true)
    expect(MENU_GROUPS.filter((g) => g.adminOnly)).toHaveLength(1)
    const analytics = MENU_GROUPS.find((g) => g.label === '数据分析')
    expect(analytics).toBeDefined()
    expect(analytics!.children).toEqual([])
    expect(analytics!.path).toBe('/analytics')
  })

  it('groupOfPath：路由映射到所属分组', () => {
    expect(groupOfPath('/basic-info/product')?.label).toBe('基础信息')
    expect(groupOfPath('/system/logs')?.label).toBe('系统管理')
    expect(groupOfPath('/orders/list')?.label).toBe('订单管理')
    expect(groupOfPath('/factory-payment/statement')?.label).toBe('工厂结算')
    expect(groupOfPath('/analytics')?.label).toBe('数据分析')
    expect(groupOfPath('/login')).toBeUndefined()
  })
})
