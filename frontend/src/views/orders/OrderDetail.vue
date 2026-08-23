<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getOrder } from '../../api/orders'
import { getTimeline } from '../../api/tracking'
import { listPayments, generateByOrder } from '../../api/factoryPayment'
import { listShipments } from '../../api/logistics'
import { listPaymentsIn } from '../../api/finance'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canEdit = computed(() => roles.value.includes('admin') || roles.value.includes('salesman') || roles.value.includes('tracker'))
const canSettle = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))
const canRegisterShipment = computed(() => roles.value.includes('admin') || roles.value.includes('tracker'))
// 后端 FinancePermission：回款登记仅 admin/finance
const canRegisterPayment = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))

const order = ref<any>(null)
const loading = ref(false)

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

function profitClass(v: any) {
  const n = Number(v)
  if (isNaN(n)) return ''
  return n >= 0 ? 'profit-positive' : 'profit-negative'
}

function statusTagType(s: string) {
  if (s === '已取消') return 'danger'
  if (s === '签收' || s === '结算' || s === '回款') return 'success'
  if (s === '接单' || s === '排产') return 'info'
  return 'warning'
}

// ---- 工厂结算 ----
function settlementTagType(s: string) {
  if (s === '已结') return 'success'
  if (s === '部分结') return 'warning'
  if (s === '未结') return 'danger'
  return 'info' // 未生成
}

const paymentMap = ref<Record<number, any>>({})
const paymentsLoading = ref(false)
const generating = ref(false)

function itemSettlement(item: any) {
  const p = paymentMap.value[item.id]
  if (!p) return { status: '未生成', payment: null }
  return { status: p.status, payment: p }
}

async function loadPayments() {
  if (!order.value?.order_no) return
  paymentsLoading.value = true
  try {
    const resp: any = await listPayments({ search: order.value.order_no, page_size: 200 })
    const m: Record<number, any> = {}
    resp.data.results.forEach((p: any) => { m[p.order_item] = p })
    paymentMap.value = m
  } finally {
    paymentsLoading.value = false
  }
}

async function generateSettlement() {
  generating.value = true
  try {
    const resp: any = await generateByOrder(order.value.id)
    ElMessage.success(`已生成 ${resp.data.created_count} 条结算单（跳过 ${resp.data.skipped_count} 条已存在）`)
    await loadPayments()
  } finally {
    generating.value = false
  }
}

// ---- 物流发货 ----
function payerTagType(p: string) {
  if (p === 'customer') return 'primary'
  if (p === 'company') return 'success'
  return 'warning'
}

function payerLabel(p: string) {
  const m: Record<string, string> = { customer: '客户', company: '公司', factory: '工厂' }
  return m[p] ?? p
}

const shipments = ref<any[]>([])
const shipmentsLoading = ref(false)

async function loadShipments() {
  if (!order.value?.order_no) return
  shipmentsLoading.value = true
  try {
    const resp: any = await listShipments({ search: order.value.order_no, page_size: 100 })
    shipments.value = resp.data.results
  } finally {
    shipmentsLoading.value = false
  }
}

function registerShipment() {
  router.push('/logistics/new?order_id=' + order.value.id)
}

// ---- 回款记录 ----
const paymentsIn = ref<any[]>([])
const paymentsInLoading = ref(false)

async function loadPaymentsIn() {
  if (!order.value?.order_no) return
  paymentsInLoading.value = true
  try {
    const resp: any = await listPaymentsIn({ search: order.value.order_no, page_size: 100 })
    paymentsIn.value = resp.data.results
  } finally {
    paymentsInLoading.value = false
  }
}

function registerPayment() {
  router.push(`/finance?register=1&order_id=${order.value.id}`)
}

async function load() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const resp: any = await getOrder(id)
    order.value = resp.data
    loadPayments()
    loadShipments()
    loadPaymentsIn()
  } finally {
    loading.value = false
  }
}

// ---- 跟单时间线 ----
const timelineLogs = ref<any[]>([])
const timelineLoading = ref(false)

async function loadTimeline() {
  const id = Number(route.params.id)
  if (!id) return
  timelineLoading.value = true
  try {
    const resp: any = await getTimeline(id)
    timelineLogs.value = resp.data
  } finally {
    timelineLoading.value = false
  }
}

onMounted(() => { load(); loadTimeline() })
</script>

<template>
  <div class="order-detail" v-loading="loading">
    <div class="detail-header">
      <el-button @click="router.push('/orders/list')">返回列表</el-button>
      <el-button v-if="canEdit" type="primary" @click="router.push(`/orders/${route.params.id}/edit`)">
        编辑订单
      </el-button>
    </div>

    <el-card v-if="order" shadow="never">
      <template #header>
        <div class="card-header">
          <span>订单详情 - {{ order.order_no }}</span>
          <el-tag v-if="order.is_cancelled" type="danger" size="small">已取消</el-tag>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
        <el-descriptions-item label="阿里状态">{{ order.ali_status || '—' }}</el-descriptions-item>
        <el-descriptions-item label="跟踪状态">
          <el-tag v-if="order.tracking_status" :type="statusTagType(order.tracking_status)" size="small">
            {{ order.tracking_status }}
          </el-tag>
          <span v-else>—</span>
        </el-descriptions-item>
        <el-descriptions-item label="订单日期">{{ order.order_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ order.customer_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="业务员">{{ order.salesman_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="跟单员">{{ order.tracker_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="订单金额(USD)">{{ fmtMoney(order.amount_usd) }}</el-descriptions-item>
        <el-descriptions-item label="运费">{{ fmtMoney(order.freight) }}</el-descriptions-item>
        <el-descriptions-item label="物流保险费">{{ fmtMoney(order.insurance) }}</el-descriptions-item>
        <el-descriptions-item label="附加费用">{{ fmtMoney(order.surcharge) }}</el-descriptions-item>
        <el-descriptions-item label="交易服务费(USD)">{{ fmtMoney(order.service_fee_usd) }}</el-descriptions-item>
        <el-descriptions-item label="运输成本">{{ fmtMoney(order.transport_cost) }}</el-descriptions-item>
        <el-descriptions-item label="承运商">{{ order.carrier || '—' }}</el-descriptions-item>
        <el-descriptions-item label="物流方式">{{ order.logistics_method || '—' }}</el-descriptions-item>
        <el-descriptions-item label="物流单号">{{ order.tracking_no || '—' }}</el-descriptions-item>
        <el-descriptions-item label="订单毛利(USD)">
          <span :class="profitClass(order.order_profit_usd)">{{ fmtMoney(order.order_profit_usd) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ order.created_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ order.updated_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ order.remark || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="order" shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>产品明细 · 工厂结算</span>
          <el-button v-if="canSettle" type="primary" size="small" :loading="generating" @click="generateSettlement">
            生成结算单
          </el-button>
        </div>
      </template>
      <el-table v-loading="paymentsLoading" :data="order.items" border stripe size="small">
        <el-table-column prop="seq" label="序号" width="70" />
        <el-table-column prop="product_no" label="产品编号" width="120" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="spec" label="规格" min-width="160" show-overflow-tooltip />
        <el-table-column prop="qty" label="数量" width="80" align="right" />
        <el-table-column label="单价(USD)" width="110" align="right">
          <template #default="{ row }">{{ fmtMoney(row.unit_price) }}</template>
        </el-table-column>
        <el-table-column label="小计(USD)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.subtotal) }}</template>
        </el-table-column>
        <el-table-column label="成本价(CNY)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.cost_price) }}</template>
        </el-table-column>
        <el-table-column label="毛利(USD)" width="110" align="right">
          <template #default="{ row }">
            <span :class="profitClass(row.profit_usd)">{{ fmtMoney(row.profit_usd) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="毛利率" width="90" align="right">
          <template #default="{ row }">
            {{ row.profit_rate != null ? (Number(row.profit_rate) * 100).toFixed(1) + '%' : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="结算状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="settlementTagType(itemSettlement(row).status)" size="small">
              {{ itemSettlement(row).status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="应付(CNY)" width="100" align="right">
          <template #default="{ row }">{{ itemSettlement(row).payment ? fmtMoney(itemSettlement(row).payment.amount_cny) : '—' }}</template>
        </el-table-column>
        <el-table-column label="已付(CNY)" width="100" align="right">
          <template #default="{ row }">{{ itemSettlement(row).payment ? fmtMoney(itemSettlement(row).payment.paid_amount) : '—' }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="order" shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>回款记录</span>
          <el-button v-if="canRegisterPayment" type="primary" size="small" @click="registerPayment">
            登记回款
          </el-button>
        </div>
      </template>
      <div v-loading="paymentsInLoading" class="payments-body">
        <el-empty v-if="!paymentsInLoading && !paymentsIn.length" description="暂无回款记录" />
        <el-table v-else :data="paymentsIn" border stripe size="small">
          <el-table-column label="期数" width="70" align="center">
            <template #default="{ row }">第 {{ row.installment }} 期</template>
          </el-table-column>
          <el-table-column prop="payment_date" label="到账日期" width="120" />
          <el-table-column label="到账金额(USD)" width="130" align="right">
            <template #default="{ row }">{{ fmtMoney(row.amount_usd) }}</template>
          </el-table-column>
          <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.note || '—' }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-card v-if="order" shadow="never" style="margin-top: 16px">
      <template #header>跟单时间线</template>
      <div v-loading="timelineLoading" class="timeline-body">
        <el-empty v-if="!timelineLoading && !timelineLogs.length" description="暂无跟单记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="log in timelineLogs"
            :key="log.id"
            :timestamp="log.created_at"
            :type="log.is_reject ? 'danger' : 'primary'"
          >
            <div class="tl-head">
              <el-tag :type="log.is_reject ? 'danger' : statusTagType(log.node)" size="small">{{ log.node }}</el-tag>
              <el-tag v-if="log.is_reject" type="danger" size="small" effect="plain">驳回</el-tag>
              <span class="tl-operator">{{ log.operator_name }}</span>
            </div>
            <p v-if="log.note" class="tl-note">{{ log.note }}</p>
            <div v-if="log.photos?.length" class="tl-photos">
              <el-image
                v-for="(p, i) in log.photos"
                :key="p.id"
                :src="p.image_url"
                :preview-src-list="log.photos.map((x: any) => x.image_url)"
                :initial-index="i"
                fit="cover"
                class="tl-photo"
                preview-teleported
              />
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <el-card v-if="order" shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>物流发货</span>
          <el-button v-if="canRegisterShipment" type="primary" size="small" @click="registerShipment">登记发货</el-button>
        </div>
      </template>
      <div v-loading="shipmentsLoading" class="shipments-body">
        <el-empty v-if="!shipmentsLoading && !shipments.length" description="暂无发货记录" />
        <el-table v-else :data="shipments" border stripe size="small">
          <el-table-column prop="seq" label="批次" width="70" align="center" />
          <el-table-column prop="carrier_name" label="国内承运商" min-width="120" show-overflow-tooltip />
          <el-table-column prop="intl_name" label="国际物流" min-width="120" show-overflow-tooltip />
          <el-table-column label="物流单号" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.tracking_no || '—' }}</template>
          </el-table-column>
          <el-table-column label="费用" width="110" align="right">
            <template #default="{ row }">{{ fmtMoney(row.cost) }}</template>
          </el-table-column>
          <el-table-column prop="cost_currency" label="币种" width="70" align="center" />
          <el-table-column label="归属" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="payerTagType(row.payer)" size="small">{{ payerLabel(row.payer) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.profit-positive {
  color: var(--el-color-success);
}
.profit-negative {
  color: var(--el-color-danger);
}
.timeline-body {
  min-height: 80px;
}
.shipments-body {
  min-height: 60px;
}
.payments-body {
  min-height: 60px;
}
.tl-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tl-operator {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.tl-note {
  margin: 8px 0;
  font-size: 14px;
  white-space: pre-wrap;
}
.tl-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tl-photo {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  cursor: pointer;
}
</style>