// 组件测试：需要真实 DOM（jsdom）
import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia } from 'pinia'
import NavRail from '../components/layout/NavRail.vue'

// 最小路由表（覆盖 menuConfig 的分组 key 前缀）
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/basic-info/product', component: { template: '<div />' } },
    { path: '/system/users', component: { template: '<div />' } },
    { path: '/orders/list', component: { template: '<div />' } },
    { path: '/analytics', component: { template: '<div />' } },
  ],
})

async function mountRail(path: string, roles: string[] = ['admin', 'salesman', 'tracker', 'finance']) {
  // user store 在创建时读取 sessionStorage（与 App 运行时一致）
  sessionStorage.setItem('roles', JSON.stringify(roles))
  await router.push(path)
  await router.isReady()
  return mount(NavRail, { global: { plugins: [router, createPinia()] } })
}

beforeEach(() => {
  sessionStorage.clear()
})

describe('NavRail', () => {
  it('渲染 8 个导航项（7 分组 + 数据分析）与 logo', async () => {
    const w = await mountRail('/basic-info/product')
    expect(w.findAll('.rail-item')).toHaveLength(8)
    expect(w.find('.rail-logo').exists()).toBe(true)
  })

  it('非 admin 隐藏系统管理分组', async () => {
    const w = await mountRail('/basic-info/product', ['salesman'])
    const labels = w.findAll('.rail-item').map((i) => i.find('.rail-label').text())
    expect(labels).not.toContain('系统管理')
    expect(labels).toHaveLength(7)
  })

  it('当前路由所属分组带 on 激活态', async () => {
    const w = await mountRail('/basic-info/product')
    const active = w.findAll('.rail-item.on')
    expect(active).toHaveLength(1)
    expect(active[0].find('.rail-label').text()).toBe('基础信息')
  })

  it('点击单页分组直达其子页', async () => {
    const w = await mountRail('/basic-info/product')
    const orders = w.findAll('.rail-item').find((i) => i.find('.rail-label').text() === '订单管理')!
    await orders.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/orders/list')
  })

  it('Esc 关闭已打开的 flyout', async () => {
    const w = await mountRail('/basic-info/product')
    const basic = w.findAll('.rail-item').find((i) => i.find('.rail-label').text() === '基础信息')!
    await basic.trigger('click')
    expect(w.find('.rail-flyout').exists()).toBe(true)
    await w.find('.nav-rail').trigger('keydown', { key: 'Escape' })
    expect(w.find('.rail-flyout').exists()).toBe(false)
  })

  it('键盘聚焦分组打开 flyout（focus-within），Esc 关闭', async () => {
    const w = await mountRail('/basic-info/product')
    const basic = w.findAll('.rail-item').find((i) => i.find('.rail-label').text() === '基础信息')!
    basic.element.focus()
    await basic.trigger('focusin')
    expect(w.find('.rail-flyout').exists()).toBe(true)
    await w.find('.nav-rail').trigger('keydown', { key: 'Escape' })
    expect(w.find('.rail-flyout').exists()).toBe(false)
  })
})
