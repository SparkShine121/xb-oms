// 组件层测试：需要真实 DOM（jsdom），不使用 node 环境
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { PhTray } from '@phosphor-icons/vue'
import PageHeader from '../components/PageHeader.vue'
import SearchToolbar from '../components/SearchToolbar.vue'
import EmptyState from '../components/EmptyState.vue'

// el-button 由 unplugin-vue-components 自动引入，附带样式入口 element-plus/es/components/*/style/css；
// 入口位于 node_modules 会被 vitest 外部化，其内部再 import theme-chalk CSS 时 Node 无法加载 .css
// → mock 掉样式入口本身（不改 vite.config）
vi.mock('element-plus/es/components/base/style/css', () => ({}))
vi.mock('element-plus/es/components/button/style/css', () => ({}))

describe('Phosphor 图标', () => {
  it('能渲染为 svg 且接受 size/weight', () => {
    const w = mount(PhTray, { props: { size: 48, weight: 'duotone' } })
    expect(w.find('svg').exists()).toBe(true)
    expect(w.attributes('width')).toBe('48')
  })
})

describe('PageHeader', () => {
  it('渲染标题、说明与右侧操作槽', () => {
    const w = mount(PageHeader, {
      props: { title: '产品库', sub: '共 12 条' },
      slots: { default: '<button class="act">新增产品</button>' },
    })
    expect(w.find('.ph-title').text()).toBe('产品库')
    expect(w.find('.ph-sub').text()).toBe('共 12 条')
    expect(w.find('.ph-actions .act').exists()).toBe(true)
  })

  it('无 sub 时不渲染说明', () => {
    const w = mount(PageHeader, { props: { title: '订单列表' } })
    expect(w.find('.ph-sub').exists()).toBe(false)
  })
})

describe('SearchToolbar', () => {
  it('渲染筛选与操作两个槽', () => {
    const w = mount(SearchToolbar, {
      slots: { filters: '<input class="f" />', actions: '<button class="a">查询</button>' },
    })
    expect(w.find('.st-filters .f').exists()).toBe(true)
    expect(w.find('.st-actions .a').exists()).toBe(true)
  })
})

describe('EmptyState', () => {
  it('渲染标题与操作按钮，点击 emit action', async () => {
    const w = mount(EmptyState, { props: { title: '还没有产品', actionText: '新增产品' } })
    expect(w.find('.es-title').text()).toBe('还没有产品')
    await w.find('button').trigger('click')
    expect(w.emitted('action')).toHaveLength(1)
  })

  it('无 actionText 时不渲染按钮', () => {
    const w = mount(EmptyState, { props: { title: '暂无数据' } })
    expect(w.find('button').exists()).toBe(false)
  })
})
