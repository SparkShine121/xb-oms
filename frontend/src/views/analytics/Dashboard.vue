<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { THEME_NAME, XBB_LIGHT_THEME } from '../../analytics/chartTheme'
import PageHeader from '../../components/PageHeader.vue'
import {
  getFactorySummary,
  getOverview,
  getSalesSummary,
  getTrackingSummary,
} from '../../api/analytics'

// 模块加载即注册，先于任何 init
echarts.registerTheme(THEME_NAME, XBB_LIGHT_THEME)

// ---------- 年度筛选 ----------
const years = [2024, 2025, 2026, 2027]
const year = ref<number | null>(new Date().getFullYear())
const yearParam = () => (year.value ? { year: year.value } : {})

const activeTab = ref('sales')
const loadedTabs = ref<Set<string>>(new Set())

// ---------- 图表实例与容器 ----------
type Chart = echarts.ECharts
const charts: Record<string, Chart | null> = {
  salesLine: null, salesPie: null,
  factoryBar: null,
  nodePie: null, dwellBar: null,
  overviewLine: null,
}
function bindChart(key: string, el: HTMLElement | undefined) {
  if (!el) return
  if (!charts[key]) charts[key] = echarts.init(el, THEME_NAME)
}
const unbindAll = () => {
  Object.keys(charts).forEach(k => { charts[k]?.dispose(); charts[k] = null })
}
const resizeAll = () => Object.values(charts).forEach(c => c?.resize())

// ---------- 销售结算表 ----------
const salesLineEl = ref<HTMLElement>()
const salesPieEl = ref<HTMLElement>()

async function loadSales() {
  try {
    const resp: any = await getSalesSummary(yearParam())
    const { by_salesman, monthly } = resp.data || { by_salesman: [], monthly: [] }
    await nextTick()
    bindChart('salesLine', salesLineEl.value)
    charts.salesLine?.setOption({
      title: { text: '月度销售/毛利趋势' },
      tooltip: { trigger: 'axis' },
      legend: {},
      xAxis: { type: 'category', data: monthly.map((m: any) => m.month) },
      yAxis: { type: 'value' },
      series: [
        { name: '销售额', type: 'line', smooth: true, data: monthly.map((m: any) => m.sales) },
        { name: '毛利', type: 'line', smooth: true, data: monthly.map((m: any) => m.profit) },
      ],
    })
    bindChart('salesPie', salesPieEl.value)
    charts.salesPie?.setOption({
      title: { text: '业务员销售额占比' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 0, top: 'middle' },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['40%', '55%'],
        data: by_salesman.map((s: any) => ({ name: s.salesman__username, value: s.total_amount })),
      }],
    })
  } catch { /* request.ts 已全局提示 */ }
}

// ---------- 工厂账单汇总 ----------
const factoryBarEl = ref<HTMLElement>()
const factoryRows = ref<any[]>([])

async function loadFactory() {
  try {
    const resp: any = await getFactorySummary(yearParam())
    factoryRows.value = resp.data || []
    await nextTick()
    bindChart('factoryBar', factoryBarEl.value)
    charts.factoryBar?.setOption({
      title: { text: '各工厂应付 vs 已付（CNY）' },
      tooltip: { trigger: 'axis' },
      legend: {},
      xAxis: { type: 'category', data: factoryRows.value.map(r => r.factory__name), axisLabel: { interval: 0, rotate: 30 } },
      yAxis: { type: 'value' },
      series: [
        { name: '应付', type: 'bar', data: factoryRows.value.map(r => r.total_amount) },
        { name: '已付', type: 'bar', data: factoryRows.value.map(r => r.total_paid) },
        { name: '未付', type: 'bar', data: factoryRows.value.map(r => r.total_unpaid) },
      ],
    })
  } catch { /* 全局提示 */ }
}

// ---------- 跟单信息汇总 ----------
const nodePieEl = ref<HTMLElement>()
const dwellBarEl = ref<HTMLElement>()

async function loadTracking() {
  try {
    const resp: any = await getTrackingSummary(yearParam())
    const { node_distribution = [], avg_dwell_days = [] } = resp.data || {}
    await nextTick()
    bindChart('nodePie', nodePieEl.value)
    charts.nodePie?.setOption({
      title: { text: '订单节点分布' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} 单 ({d}%)' },
      legend: { orient: 'vertical', right: 0, top: 'middle' },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['40%', '55%'],
        data: node_distribution.map((n: any) => ({ name: n.node, value: n.count })),
      }],
    })
    bindChart('dwellBar', dwellBarEl.value)
    charts.dwellBar?.setOption({
      title: { text: '各节点平均停留时长（天）' },
      tooltip: { trigger: 'axis' },
      grid: { left: 80 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: avg_dwell_days.map((d: any) => d.node) },
      series: [{ type: 'bar', data: avg_dwell_days.map((d: any) => d.avg_days) }],
    })
  } catch { /* 全局提示 */ }
}

// ---------- 总览 ----------
const overviewLineEl = ref<HTMLElement>()
const ov = ref({ total_orders: 0, total_sales: 0, total_profit: 0 })

async function loadOverview() {
  try {
    const resp: any = await getOverview(yearParam())
    const d = resp.data || { total_orders: 0, total_sales: 0, total_profit: 0, monthly: [] }
    ov.value = { total_orders: d.total_orders, total_sales: d.total_sales, total_profit: d.total_profit }
    await nextTick()
    bindChart('overviewLine', overviewLineEl.value)
    charts.overviewLine?.setOption({
      title: { text: '月度销售/毛利趋势' },
      tooltip: { trigger: 'axis' },
      legend: {},
      xAxis: { type: 'category', data: (d.monthly || []).map((m: any) => m.month) },
      yAxis: { type: 'value' },
      series: [
        { name: '销售额', type: 'line', smooth: true, areaStyle: {}, data: (d.monthly || []).map((m: any) => m.sales) },
        { name: '毛利', type: 'line', smooth: true, areaStyle: {}, data: (d.monthly || []).map((m: any) => m.profit) },
      ],
    })
  } catch { /* 全局提示 */ }
}

// ---------- Tab 懒加载 + 年份切换刷新 ----------
const loaders: Record<string, () => Promise<void>> = {
  sales: loadSales,
  factory: loadFactory,
  tracking: loadTracking,
  overview: loadOverview,
}

async function renderActiveTab(tab?: string) {
  const name = tab || activeTab.value
  await loaders[name]?.()
  loadedTabs.value.add(name)
  resizeAll()
}

function onTabChange(name: string | number) {
  void renderActiveTab(String(name))
}

function onYearChange() {
  loadedTabs.value.clear()
  void renderActiveTab()
}

onMounted(async () => {
  await renderActiveTab('sales')
  window.addEventListener('resize', resizeAll)
})
onBeforeUnmount(unbindAll)

function fmtMoney(v: number): string {
  return v == null ? '-' : v.toLocaleString('en-US', { maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="analytics-dashboard">
    <PageHeader title="数据分析">
      <el-select v-model="year" placeholder="全部年份" clearable style="width: 140px" @change="onYearChange">
        <el-option v-for="y in years" :key="y" :label="`${y} 年`" :value="y" />
      </el-select>
    </PageHeader>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- 销售结算表 -->
      <el-tab-pane label="销售结算表" name="sales">
        <div class="chart-row">
          <div class="chart-box tall">
            <div ref="salesLineEl" class="chart" />
          </div>
          <div class="chart-box tall">
            <div ref="salesPieEl" class="chart" />
          </div>
        </div>
      </el-tab-pane>

      <!-- 工厂账单汇总 -->
      <el-tab-pane label="工厂账单汇总" name="factory">
        <div class="chart-box wide">
          <div ref="factoryBarEl" class="chart tall-chart" />
        </div>
        <el-table :data="factoryRows" border size="small" style="margin-top: 12px">
          <el-table-column prop="factory__name" label="工厂" min-width="160" />
          <el-table-column prop="total_amount" label="应付（CNY）" align="right" :formatter="(r: any) => fmtMoney(r.total_amount)" />
          <el-table-column prop="total_paid" label="已付（CNY）" align="right" :formatter="(r: any) => fmtMoney(r.total_paid)" />
          <el-table-column prop="total_unpaid" label="未付（CNY）" align="right" :formatter="(r: any) => fmtMoney(r.total_unpaid)" />
          <el-table-column prop="payment_count" label="结算单数" align="right" />
        </el-table>
      </el-tab-pane>

      <!-- 跟单信息汇总 -->
      <el-tab-pane label="跟单信息汇总" name="tracking">
        <div class="chart-row">
          <div class="chart-box tall">
            <div ref="nodePieEl" class="chart" />
          </div>
          <div class="chart-box tall">
            <div ref="dwellBarEl" class="chart" />
          </div>
        </div>
      </el-tab-pane>

      <!-- 总览 -->
      <el-tab-pane label="总览" name="overview">
        <div class="kpi-row">
          <div class="kpi">
            <div class="kpi-label">订单总数</div>
            <div class="kpi-value num">{{ ov.total_orders }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">总销售额（USD）</div>
            <div class="kpi-value num">{{ fmtMoney(ov.total_sales) }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">总毛利（USD）</div>
            <div class="kpi-value num">{{ fmtMoney(ov.total_profit) }}</div>
          </div>
        </div>
        <div class="chart-box wide">
          <div ref="overviewLineEl" class="chart tall-chart" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
/* KPI 无卡指标行（规范 §7：数字 22-24px/700 + 1px 分隔线，不套卡片） */
.kpi-row {
  display: flex;
  padding: 2px 0 16px;
}
.kpi {
  flex: 1;
  padding: 2px 24px;
  border-left: 1px solid var(--line);
}
.kpi:first-child {
  padding-left: 0;
  border-left: none;
}
.kpi-label {
  font-size: 12.5px;
  color: var(--mut);
}
.kpi-value {
  font-size: 23px;
  font-weight: 700;
  margin-top: 4px;
  color: var(--txt);
}
/* 图表容器=内部块（规范 §1.5 --r-in）；内容区本身是 --panel 面板，根容器不再套卡 */
.chart-row {
  display: flex;
  gap: 14px;
}
.chart-box {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: var(--r-in);
  padding: 8px;
}
.chart-box.wide {
  margin-top: 16px;
}
.chart {
  width: 100%;
  height: 320px;
}
.chart.tall-chart {
  height: 380px;
}
</style>
