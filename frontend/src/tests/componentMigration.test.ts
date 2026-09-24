// @vitest-environment node
// 迁移不变量：视图层不得再复制工具栏/分页样式块（错题集 2026-09-07「同类 UI 优先全局化」）
import { describe, expect, it } from 'vitest'

const views = import.meta.glob('../views/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>

describe('组件迁移不变量', () => {
  it('没有页面同时复制 .toolbar 与 .toolbar-right 样式块', () => {
    const offenders = Object.entries(views)
      .filter(([, src]) => /\.toolbar\s*\{/.test(src) && /\.toolbar-right\s*\{/.test(src))
      .map(([path]) => path)
    expect(offenders).toEqual([])
  })

  it('列表页不再自带 .pager 样式块', () => {
    const offenders = Object.entries(views)
      .filter(([, src]) => /\.pager\s*\{/.test(src))
      .map(([path]) => path)
    expect(offenders).toEqual([])
  })
})
