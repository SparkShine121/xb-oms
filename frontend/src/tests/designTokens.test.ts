// @vitest-environment node
// 设计令牌锁定测试：直接读文件文本断言（不依赖 DOM，node 环境最快）
// 规范来源：《风格重构/风格拆解清单.md》§1；颜色值变更必须先改规范再改这里
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { THEME_NAME, CHART_COLORS, XBB_LIGHT_THEME } from '../analytics/chartTheme'

const css = readFileSync(new URL('../style.css', import.meta.url), 'utf8')
const dashboardSrc = readFileSync(new URL('../views/analytics/Dashboard.vue', import.meta.url), 'utf8')
const mobileLayoutSrc = readFileSync(new URL('../layouts/MobileLayout.vue', import.meta.url), 'utf8')

const allViewSources: Record<string, string> = {
  ...(import.meta.glob('../views/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>),
  ...(import.meta.glob('../components/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>),
  ...(import.meta.glob('../layouts/**/*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>),
  ...(import.meta.glob('../App.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>),
}

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
    expect(contrast(token('dim'), token('panel3'))).toBeGreaterThanOrEqual(4.5)
  })

  it('语义 tint 与其余兼容别名锁定', () => {
    expect(token('success-tint')).toBe('rgba(23, 128, 61, 0.12)')
    expect(token('warning-tint')).toBe('rgba(194, 65, 12, 0.12)')
    expect(token('danger-tint')).toBe('rgba(192, 53, 43, 0.12)')
    expect(token('info-tint')).toBe('rgba(29, 78, 216, 0.1)')
    expect(token('brand-500')).toBe('var(--lime-text)')
    expect(token('brand-700')).toBe('var(--lime-text)')
    expect(token('brand-800')).toBe('var(--txt)')
    expect(token('accent')).toBe('var(--info)')
    expect(token('text-700')).toBe('var(--txt)')
    expect(token('text-500')).toBe('var(--mut)')
    expect(token('text-400')).toBe('var(--dim)')
    expect(token('surface-muted')).toBe('var(--panel2)')
    expect(token('radius-sm')).toBe('var(--r-ctl)')
    expect(token('radius')).toBe('var(--r-in)')
    expect(token('radius-lg')).toBe('var(--r-card)')
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

  it('旧令牌名保留为兼容别名（仅 2 个布局文件仍引用，M6 清理）', () => {
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

describe('排版与细节', () => {
  it('基础排版：行高、.num 数字类、标题防孤字', () => {
    expect(css).toMatch(/html,\s*body\s*\{[^}]*line-height:\s*1\.65/)
    expect(css).toMatch(/\.num\s*\{[^}]*tabular-nums/)
    expect(css).toMatch(/h1,\s*h2,\s*h3\s*\{[^}]*text-wrap:\s*balance/)
  })

  it('focus 可见环（可达性强制项）', () => {
    expect(css).toMatch(/:focus-visible\s*\{[^}]*outline:\s*2px solid var\(--lime-text\)/)
    expect(css).toMatch(/:focus-visible\s*\{[^}]*outline-offset:\s*2px/)
  })

  it('toast 保持 alert 交互（居中+遮罩），仅换配色', () => {
    expect(css).toContain('top: 50% !important')
    expect(css).toContain('.global-toast-mask')
    expect(css).toMatch(/--el-message-bg-color:\s*var\(--panel\)/)
    expect(css).not.toMatch(/\.el-message\s*\{[^}]*background:\s*#fff/)
  })

  it('旧令牌名零残留：var(--brand-600) 不再出现在 style.css（Task 3 后）', () => {
    expect(css).not.toContain('var(--brand-600)')  // Task 3 后旧名零残留（别名定义处也不含该串）
  })

  it('深底强调对比度：lime-deep 对 panel3 达 AA', () => {
    expect(contrast(token('lime-deep'), token('panel3'))).toBeGreaterThanOrEqual(4.5)
  })

  it('Vant 映射：primary 深橄榄 + 表面令牌 + 按钮 lime 填充', () => {
    expect(token('van-primary-color')).toBe('var(--lime-text)')
    expect(token('van-background')).toBe('var(--canvas)')
    expect(token('van-background-2')).toBe('var(--panel)')
    expect(token('van-text-color')).toBe('var(--txt)')
    expect(token('van-border-color')).toBe('var(--line)')
    expect(token('van-button-primary-background')).toBe('var(--lime)')
    expect(token('van-button-primary-color')).toBe('var(--lime-ink)')
    expect(token('van-tabbar-height')).toBe('52px')
  })
})

describe('硬编码色清理（第一批）', () => {
  const read = (p: string) => readFileSync(new URL(p, import.meta.url), 'utf8')

  it('Login.vue 不再有旧蓝色渐变', () => {
    const sfc = read('../views/Login.vue')
    expect(sfc).not.toContain('#1e3a8a')
    expect(sfc).not.toContain('#2563eb')
    expect(sfc).toContain('var(--canvas)')
    expect(sfc).toContain('var(--lime-tint)')
  })

  it('MobileHome.vue banner 不再用 Vant 旧蓝', () => {
    const sfc = read('../views/m/MobileHome.vue')
    expect(sfc).not.toContain('#1989fa')
    expect(sfc).toContain('linear-gradient(135deg, var(--lime)')
    expect(sfc).not.toContain('#323233')
  })

  it('favicon 换成 lime 方块', () => {
    const svg = read('../../public/favicon.svg')
    expect(svg).not.toContain('#863bff')
    expect(svg).toContain('#CBF74E')
  })
})

describe('M2 全局 EP 微调', () => {
  it('loading 遮罩与 disabled 底色走令牌', () => {
    expect(token('el-mask-color')).toBe('rgba(252, 252, 253, 0.72)')
    expect(token('el-disabled-bg-color')).toBe('var(--panel3)')
  })

  it('输入框聚焦外环用高 specificity 压过 EP 的 is-focus 规则', () => {
    expect(css).toMatch(/\.el-input \.el-input__wrapper\.is-focus[\s\S]{0,200}?box-shadow:\s*0 0 0 1px var\(--lime-text\) inset,\s*0 0 0 3px var\(--lime-tint\)/)
    expect(css).toMatch(/\.el-select \.el-select__wrapper\.is-focused[\s\S]{0,200}?box-shadow:\s*0 0 0 1px var\(--lime-text\) inset,\s*0 0 0 3px var\(--lime-tint\)/)
  })

  it('range 选择器（daterange 根元素即 .el-input__wrapper）不丢聚焦环', () => {
    // daterange 的根元素本身就是 .el-input__wrapper（无 .el-input 父节点），必须单独列出
    expect(css).toMatch(/\.el-range-editor\.el-input__wrapper\.is-focus[\s\S]{0,200}?box-shadow:\s*0 0 0 1px var\(--lime-text\) inset,\s*0 0 0 3px var\(--lime-tint\)/)
    expect(css).toMatch(/\.el-range-editor\.el-input__wrapper:focus-within[\s\S]{0,200}?box-shadow:\s*0 0 0 1px var\(--lime-text\) inset,\s*0 0 0 3px var\(--lime-tint\)/)
  })
})

describe('门禁：EP 覆盖必须双类（防同 specificity 被后加载反超）', () => {
  it('style.css 中针对 .el-* 组件的覆盖不得是单类选择器', () => {
    // 错题集 2026-09-22/2026-09-24：完整包 import 或任何加载顺序变化，都会让同 specificity 的
    // 覆盖被 EP 后加载的样式静默反超（按钮/表格/聚焦环三次踩坑）。
    // 门禁：凡选择器引用 .el-*（或声明 --el-* 变量）的规则，选择器必须含 ≥2 个类
    //（双类 .el-x.el-x、祖先限定、复合均可）；:root 与 .van-* 不在本门禁范围。
    const cssNoComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
    const ruleRe = /([^{}]+)\{([^{}]*)\}/g
    const offenders: string[] = []
    let m: RegExpExecArray | null
    while ((m = ruleRe.exec(cssNoComments)) !== null) {
      const selectorText = m[1].trim().replace(/\s+/g, ' ')
      const body = m[2]
      const touchesEp = selectorText.includes('.el-') || /--el-[a-z-]/.test(body)
      if (!touchesEp) continue
      for (const part of selectorText.split(',')) {
        const sel = part.trim()
        if (sel === ':root' || !sel.includes('.el-')) continue
        const classCount = (sel.match(/\.[a-z][a-z0-9_-]*/gi) || []).length
        if (classCount < 2) offenders.push(sel)
      }
    }
    expect(offenders).toEqual([])
  })
})

describe('ECharts 浅色主题（chartTheme.ts ↔ style.css 令牌一致性）', () => {
  it('主题名与序列色为规范值（lime-text/info/success/warning 四档）', () => {
    expect(THEME_NAME).toBe('xbb-light')
    expect(CHART_COLORS).toEqual([token('lime-text'), token('info'), token('success'), token('warning')])
  })

  it('主题色值与 style.css 令牌逐值一致（canvas 不能用 CSS 变量）', () => {
    expect(XBB_LIGHT_THEME.backgroundColor).toBe('transparent')
    expect(XBB_LIGHT_THEME.color).toBe(CHART_COLORS)
    expect(XBB_LIGHT_THEME.title.textStyle).toMatchObject({ color: token('txt'), fontSize: 14, fontWeight: 600 })
    expect(XBB_LIGHT_THEME.legend.textStyle).toMatchObject({ color: token('mut') })
    expect(XBB_LIGHT_THEME.categoryAxis.axisLine.lineStyle.color).toBe(token('line'))
    expect(XBB_LIGHT_THEME.valueAxis.splitLine.lineStyle.color).toBe(token('line'))
    expect(XBB_LIGHT_THEME.tooltip.backgroundColor).toBe(token('panel'))
    expect(XBB_LIGHT_THEME.tooltip.borderColor).toBe(token('line2'))
    expect(XBB_LIGHT_THEME.tooltip.textStyle).toMatchObject({ color: token('txt') })
  })

  it('主题字体栈与 style.css 一致（canvas 不继承页面 font-family）', () => {
    // style.css 的 font-family 跨行书写，先折叠空白再比较
    const pageFont = css.match(/font-family:\s*([^;]+);/)?.[1]?.replace(/\s+/g, ' ').trim()
    expect(pageFont).toBeTruthy()
    expect(XBB_LIGHT_THEME.textStyle?.fontFamily).toBe(pageFont)
  })
})

describe('仪表盘 M4 改造', () => {
  it('KPI 区不套卡（无 el-card / el-row），改无卡指标行', () => {
    expect(dashboardSrc).not.toContain('<el-card')
    expect(dashboardSrc).not.toContain('<el-row')
    expect(dashboardSrc).not.toContain('el-col')
    expect(dashboardSrc).toContain('kpi-row')
  })

  it('六图统一启用 xbb-light 主题', () => {
    expect(dashboardSrc).toContain('echarts.init(el, THEME_NAME)')
    expect(dashboardSrc).toContain("echarts.registerTheme(THEME_NAME, XBB_LIGHT_THEME)")
  })

  it('页头复用 PageHeader 且文案零改动，KPI 标签原文保留', () => {
    expect(dashboardSrc).toContain('<PageHeader title="数据分析">')
    expect(dashboardSrc).not.toContain('dashboard-filters')
    for (const label of ['订单总数', '总销售额（USD）', '总毛利（USD）']) {
      expect(dashboardSrc).toContain(label)
    }
  })
})

describe('门禁：全站视图零硬编码色', () => {
  it('views/components/layouts 源码无硬编码色（零豁免）', () => {
    expect(Object.keys(allViewSources).length).toBeGreaterThan(20)
    const offenders: string[] = []
    const NAMED_COLORS = 'black|white|red|green|blue|yellow|orange|purple|pink|gray|grey|cyan|magenta|silver|gold|teal|navy|olive|lime|aqua|fuchsia|crimson|indigo|violet|tomato|salmon|coral'
    for (const [path, src] of Object.entries(allViewSources)) {
      const s = src
        .replace(/<!--[\s\S]*?-->/g, '')   // HTML 注释
        .replace(/\/\*[\s\S]*?\*\//g, '')  // CSS 块注释
        .replace(/\/\/[^\n]*/g, '')        // 行注释
      if (new RegExp(`#[0-9a-fA-F]{3,8}\\b|\\brgba?\\(|\\bhsla?\\(|:\\s*(?:${NAMED_COLORS})\\b`).test(s)) offenders.push(path)
    }
    expect(offenders).toEqual([])
  })
})

describe('移动端 tabbar（M5）', () => {
  it('tabbar 标签 10.5px + 不换行（"工厂结算"4 字标签在 375px 不折行）', () => {
    expect(mobileLayoutSrc).toContain('van-tabbar-item__text')
    expect(mobileLayoutSrc).toMatch(/van-tabbar-item__text[\s\S]{0,200}?font-size:\s*10\.5px/)
    expect(mobileLayoutSrc).toMatch(/van-tabbar-item__text[\s\S]{0,200}?white-space:\s*nowrap/)
  })
})

describe('可达性：prefers-reduced-motion（规范 §6 强制项）', () => {
  it('全局降级规则存在且压平 animation/transition', () => {
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*animation-duration:\s*0\.01ms/)
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*transition-duration:\s*0\.01ms/)
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*animation-iteration-count:\s*1/)
  })
})
