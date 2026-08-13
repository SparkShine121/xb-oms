<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrder } from '../../api/orders'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canEdit = computed(() => roles.value.includes('admin') || roles.value.includes('salesman') || roles.value.includes('tracker'))

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

async function load() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const resp: any = await getOrder(id)
    order.value = resp.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
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
      <template #header>产品明细</template>
      <el-table :data="order.items" border stripe size="small">
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
      </el-table>
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
</style>