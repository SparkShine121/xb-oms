// @vitest-environment node
// 迁移不变量：视图层与公共组件层不得再复制工具栏/分页样式块（错题集 2026-09-07「同类 UI 优先全局化」）
// 注意：正则用 `[,{]` 收边，可命中合并选择器（如 `.toolbar, .toolbar-right {`）；
// `.tracking-toolbar` 这类 `-toolbar` 后缀类不含裸 `.toolbar`，不受影响
import { describe, expect, it } from 'vitest'

const views = import.meta.glob('../views/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>
const components = import.meta.glob('../components/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>
const sources = { ...views, ...components }

describe('组件迁移不变量', () => {
  it('视图层/组件层不再自带 .toolbar 样式块（公共组件 SearchToolbar 之外零例外）', () => {
    const offenders = Object.entries(sources)
      .filter(([, src]) => /\.toolbar\s*[,{]/.test(src))
      .map(([path]) => path)
    expect(offenders).toEqual([])
  })

  it('列表页不再自带 .pager 样式块', () => {
    const offenders = Object.entries(sources)
      .filter(([, src]) => /\.pager\s*[,{]/.test(src))
      .map(([path]) => path)
    expect(offenders).toEqual([])
  })
})
