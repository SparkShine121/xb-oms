// ECharts 浅色主题常量（规范《风格拆解清单.md》§7 仪表盘）。
// ECharts 为 canvas 渲染，CSS 变量在 canvas 中无效——色值必须与 style.css 令牌逐值一致，
// 由 designTokens.test.ts「ECharts 浅色主题」describe 锁定（改令牌时同步此处，测试会红）。
// 双轨制：序列色是文字型强调，lime 档用深橄榄 --lime-text（非 --lime 填充色）。
export const THEME_NAME = 'xbb-light'

/** 序列色 4 档：lime-text / info / success / warning（规范 §7） */
export const CHART_COLORS = ['#5b7600', '#1d4ed8', '#17803d', '#c2410c']

export const XBB_LIGHT_THEME = {
  backgroundColor: 'transparent',
  color: CHART_COLORS,
  title: {
    textStyle: { color: '#17191e', fontSize: 14, fontWeight: 600 },
  },
  legend: {
    textStyle: { color: '#5b616b', fontSize: 12 },
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: 'rgba(17, 19, 23, 0.08)' } },
    axisTick: { show: false },
    axisLabel: { color: '#5b616b' },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#5b616b' },
    splitLine: { lineStyle: { color: 'rgba(17, 19, 23, 0.08)' } },
  },
  tooltip: {
    backgroundColor: '#fcfcfd',
    borderColor: 'rgba(17, 19, 23, 0.14)',
    borderWidth: 1,
    padding: [8, 12],
    textStyle: { color: '#17191e', fontSize: 12.5 },
    extraCssText: 'box-shadow: 0 12px 32px -8px rgba(20, 24, 32, 0.14); border-radius: 12px;',
  },
}
