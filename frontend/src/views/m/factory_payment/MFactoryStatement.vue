<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listPayments, getStatement } from '../../../api/factoryPayment'
import { listFactories } from '../../../api/basicInfo'

const router = useRouter()

function statusTagType(s: string) {
  if (s === '已结') return 'success'
  if (s === '部分结') return 'warning'
  return 'danger'
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

const rows = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 20

const summary = ref({ total_amount: '0', total_paid: '0', total_unpaid: '0', count: 0 })
const summaryCards = computed(() => [
  { label: '应付总额(CNY)', value: fmtMoney(summary.value.total_amount), cls: '' },
  { label: '已付总额(CNY)', value: fmtMoney(summary.value.total_paid), cls: 'paid' },
  { label: '未付总额(CNY)', value: fmtMoney(summary.value.total_unpaid), cls: 'unpaid' },
  { label: '结算单数', value: String(summary.value.count ?? 0), cls: '' },
])

const factoryFilter = ref<number>(0)
const factoryOptions = ref<{ text: string; value: number }[]>([])
const dateRange = ref<[string, string] | null>(null)
const showCalendar = ref(false)

async function onLoad() {
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      factory: factoryFilter.value || undefined,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    }
    const [listResp, stmtResp]: any[] = await Promise.all([
      listPayments(params),
      getStatement({
        factory: factoryFilter.value || undefined,
        start_date: dateRange.value?.[0],
        end_date: dateRange.value?.[1],
      }),
    ])
    rows.value = rows.value.concat(listResp.data.results)
    summary.value = stmtResp.data
    if (listResp.data.next) page.value += 1
    else finished.value = true
  } catch {
    // 加载失败停止自动重试（错误提示由全局拦截器处理）
    finished.value = true
  } finally {
    loading.value = false
  }
}

async function loadFactories() {
  const resp: any = await listFactories({ page: 1, page_size: 200 })
  factoryOptions.value = [
    { text: '全部工厂', value: 0 },
    ...(resp.data.results ?? []).map((f: any) => ({ text: f.name, value: f.id })),
  ]
}

// 筛选/日期切换：重置分页并重新加载
function resetAndLoad() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function fmtDate(d: Date) {
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

function onCalendarConfirm(dates: Date[]) {
  if (dates && dates.length === 2) {
    dateRange.value = [fmtDate(dates[0]), fmtDate(dates[1])]
  }
  showCalendar.value = false
  resetAndLoad()
}

function clearDateRange() {
  dateRange.value = null
  resetAndLoad()
}

function goDetail(id: number) {
  router.push(`/m/factory-payment/${id}`)
}

onMounted(loadFactories)
</script>

<template>
  <div class="m-factory-statement">
    <van-nav-bar title="工厂对账单" left-arrow @click-left="router.back()" />

    <van-dropdown-menu>
      <van-dropdown-item v-model="factoryFilter" :options="factoryOptions" @change="resetAndLoad" />
    </van-dropdown-menu>

    <van-cell
      is-link
      center
      class="date-cell"
      :title="'日期范围'"
      :value="dateRange ? `${dateRange[0]} 至 ${dateRange[1]}` : '不限'"
      @click="showCalendar = true"
    >
      <template v-if="dateRange" #icon>
        <van-icon name="clear" size="16" @click.stop="clearDateRange" />
      </template>
    </van-cell>

    <van-grid :column-num="2" :border="false" class="summary-grid">
      <van-grid-item v-for="c in summaryCards" :key="c.label">
        <div class="summary-card">
          <div class="summary-label">{{ c.label }}</div>
          <div class="summary-value" :class="c.cls">{{ c.value }}</div>
        </div>
      </van-grid-item>
    </van-grid>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="rows.length ? '没有更多了' : ''"
      @load="onLoad"
    >
      <van-cell v-for="item in rows" :key="item.id" is-link center @click="goDetail(item.id)">
        <template #title>
          <div class="cell-title">
            <span class="order-no">{{ item.order_no }}</span>
            <van-tag :type="statusTagType(item.status)" size="medium" plain>{{ item.status }}</van-tag>
          </div>
        </template>
        <template #label>
          <span class="cell-label">{{ item.factory_name || '—' }} · {{ item.product_no || '—' }}</span>
        </template>
        <template #value>
          <div class="amount-wrap">
            <div class="amount">应付 ¥{{ fmtMoney(item.amount_cny) }}</div>
            <div class="paid">已付 ¥{{ fmtMoney(item.paid_amount) }}</div>
          </div>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="finished && !rows.length" description="暂无结算单" />

    <!-- 日期范围选择 -->
    <van-popup v-model:show="showCalendar" position="bottom" round>
      <van-calendar
        type="range"
        :show-confirm="true"
        :min-date="new Date(2020, 0, 1)"
        :max-date="new Date()"
        @confirm="onCalendarConfirm"
        @close="showCalendar = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.date-cell {
  margin: 4px 0;
}
.summary-grid {
  margin: 0 16px;
}
.summary-card {
  padding: 12px 8px;
  text-align: center;
  background: #fff;
  border-radius: 8px;
}
.summary-label {
  font-size: 12px;
  color: #969799;
  margin-bottom: 6px;
}
.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}
.summary-value.paid {
  color: #07c160;
}
.summary-value.unpaid {
  color: #ee0a24;
}
.cell-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.order-no {
  font-weight: 600;
  color: #323233;
}
.cell-label {
  color: #969799;
  font-size: 13px;
}
.amount-wrap {
  text-align: right;
}
.amount {
  color: #1989fa;
  font-weight: 600;
}
.paid {
  color: #969799;
  font-size: 12px;
  margin-top: 2px;
}
</style>
