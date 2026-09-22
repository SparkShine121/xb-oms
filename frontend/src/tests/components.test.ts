// 组件层测试：需要真实 DOM（jsdom），不使用 node 环境
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { PhTray } from '@phosphor-icons/vue'

describe('Phosphor 图标', () => {
  it('能渲染为 svg 且接受 size/weight', () => {
    const w = mount(PhTray, { props: { size: 48, weight: 'duotone' } })
    expect(w.find('svg').exists()).toBe(true)
    expect(w.attributes('width')).toBe('48')
  })
})
