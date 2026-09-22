// @vitest-environment node
// 设计令牌锁定测试：直接读文件文本断言（不依赖 DOM，node 环境最快）
// 规范来源：《风格重构/风格拆解清单.md》§1；颜色值变更必须先改规范再改这里
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

const css = readFileSync(new URL('../style.css', import.meta.url), 'utf8')

function token(name: string): string {
  const m = css.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`))
  if (!m) throw new Error(`缺少令牌 --${name}`)
  return m[1].trim().toLowerCase()
}

function luminance(hex: string): number {
  const h = hex.replace('#', '')
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255)
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4))
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

describe('设计令牌（浅色版）', () => {
  it('表面与文字令牌为规范值', () => {
    expect(token('canvas')).toBe('#f1f2f4')
    expect(token('panel')).toBe('#fcfcfd')
    expect(token('panel2')).toBe('#f5f6f8')
    expect(token('panel3')).toBe('#ecedf0')
    expect(token('txt')).toBe('#17191e')
    expect(token('mut')).toBe('#5b616b')
    expect(token('dim')).toBe('#666c75')
  })

  it('lime 家族与语义色为规范值', () => {
    expect(token('lime')).toBe('#cbf74e')
    expect(token('lime-ink')).toBe('#15170a')
    expect(token('lime-text')).toBe('#5b7600')
    expect(token('lime-deep')).toBe('#4a6100')
    expect(token('lime-hover')).toBe('#bceb3a')
    expect(token('lime-active')).toBe('#addc28')
    expect(token('success')).toBe('#17803d')
    expect(token('warning')).toBe('#c2410c')
    expect(token('danger')).toBe('#c0352b')
    expect(token('info')).toBe('#1d4ed8')
  })

  it('禁止纯白面板与纯黑阴影', () => {
    expect(token('panel')).not.toMatch(/^#(fff|ffffff)$/)
    for (const name of ['shadow-card', 'shadow-pop', 'shadow-overlay']) {
      expect(token(name)).not.toContain('rgba(0, 0, 0')
      expect(token(name)).not.toContain('rgba(0,0,0')
    }
  })

  it('对比度全部达 WCAG AA', () => {
    const panel = token('panel')
    expect(contrast(token('txt'), panel)).toBeGreaterThanOrEqual(7)
    expect(contrast(token('mut'), panel)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('dim'), panel)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('lime-text'), panel)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('lime-ink'), token('lime'))).toBeGreaterThanOrEqual(7)
    expect(contrast(token('lime-deep'), token('panel3'))).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('success'), panel)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('warning'), panel)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('danger'), panel)).toBeGreaterThanOrEqual(4.5)
  })

  it('边线/圆角/阴影/缓动为规范值', () => {
    expect(token('line')).toBe('rgba(17, 19, 23, 0.08)')
    expect(token('line2')).toBe('rgba(17, 19, 23, 0.14)')
    expect(token('lime-tint')).toBe('rgba(163, 209, 26, 0.14)')
    expect(token('r-frame')).toBe('32px')
    expect(token('r-card')).toBe('24px')
    expect(token('r-in')).toBe('16px')
    expect(token('r-nav')).toBe('14px')
    expect(token('r-ctl')).toBe('12px')
    expect(token('r-sm')).toBe('10px')
    expect(token('ease')).toBe('cubic-bezier(0.22, 1, 0.36, 1)')
    expect(token('shadow-card')).toBe('0 1px 2px rgba(20, 24, 32, 0.05), 0 1px 3px rgba(20, 24, 32, 0.04)')
    expect(token('shadow-pop')).toBe('0 12px 32px -8px rgba(20, 24, 32, 0.14)')
    expect(token('shadow-overlay')).toBe('0 24px 64px -12px rgba(20, 24, 32, 0.22)')
  })

  it('旧令牌名保留为兼容别名（35 个页面依赖）', () => {
    expect(token('brand-600')).toBe('var(--lime-text)')
    expect(token('text-900')).toBe('var(--txt)')
    expect(token('border')).toBe('var(--line)')
    expect(token('surface')).toBe('var(--panel)')
    expect(token('bg-page')).toBe('var(--canvas)')
  })
})

describe('Element Plus 映射（浅色版）', () => {
  it('primary 双轨制：变量用深橄榄，按钮填充用 lime', () => {
    expect(token('el-color-primary')).toBe('var(--lime-text)')
    const btn = css.match(/\.el-button--primary\s*\{([^}]+)\}/)?.[1] ?? ''
    expect(btn).toContain('--el-button-bg-color: var(--lime)')
    expect(btn).toContain('--el-button-text-color: var(--lime-ink)')
    expect(btn).toContain('--el-button-hover-bg-color: var(--lime-hover)')
  })

  it('表面/文字/边框/圆角映射到位', () => {
    expect(token('el-bg-color')).toBe('var(--panel)')
    expect(token('el-bg-color-page')).toBe('var(--canvas)')
    expect(token('el-text-color-primary')).toBe('var(--txt)')
    expect(token('el-border-color')).toBe('var(--line)')
    expect(token('el-border-radius-base')).toBe('var(--r-ctl)')
    expect(token('el-font-size-base')).toBe('13px')
    expect(token('el-font-family')).toBe('inherit')
  })

  it('表格变量与旧品牌蓝清理', () => {
    expect(token('el-table-header-bg-color')).toBe('var(--panel2)')
    expect(token('el-table-row-hover-bg-color')).toBe('var(--panel2)')
    expect(css).not.toContain('#2563eb')  // 旧品牌蓝彻底移除
    expect(css).toMatch(/\.el-table th\.el-table__cell\s*\{[^}]*font-size:\s*12\.5px/)
    expect(css).toMatch(/\.el-table th\.el-table__cell\s*\{[^}]*font-weight:\s*600/)
    expect(css).toMatch(/\.el-table \.el-table__cell\s*\{[^}]*padding:\s*8px 0/)
  })

  it('EP 语义色与 primary 色阶映射', () => {
    expect(token('el-color-success')).toBe('var(--success)')
    expect(token('el-color-warning')).toBe('var(--warning)')
    expect(token('el-color-danger')).toBe('var(--danger)')
    expect(token('el-color-error')).toBe('var(--danger)')
    expect(token('el-color-info')).toBe('var(--info)')
    expect(token('el-color-primary-light-3')).toBe('#7c9a1f')
    expect(token('el-color-primary-light-9')).toBe('#f2f6e6')
    expect(token('el-color-primary-dark-2')).toBe('var(--lime-deep)')
    expect(token('el-input-bg-color')).toBe('var(--panel2)')
    expect(token('el-input-focus-border-color')).toBe('var(--lime-text)')
  })
})
