// 组件层测试：需要真实 DOM（jsdom），不使用 node 环境
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { PhTray } from '@phosphor-icons/vue'
import PageHeader from '../components/PageHeader.vue'

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
