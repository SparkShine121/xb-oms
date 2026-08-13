<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrder } from '../../../api/orders'
import { useUserStore } from '../../../stores/user'

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
  if (s === '接单' || s === '排产') return 'primary'
  return 'warning'
}

function fmtRate(v: any) {
  if (v == null || v === '') return '—'
  return (Number(v) * 100).toFixed(1) + '%'
}

async function load() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const resp: any = await getOrder(id)
    order.value = resp.data
  } catch {
    // 错误提示由全局拦截器处理；order 保持 null，下面渲染失败占位
    order.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="m-order-detail">
    <van-nav-bar title="订单详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" />
    </div>

    <template v-else-if="order">
      <van-cell-group inset title="订单信息" class="info-group">
        <van-cell title="订单号" :value="order.order_no" />
        <van-cell title="阿里状态" :value="order.ali_status || '—'" />
        <van-cell title="跟踪状态">
          <template #value>
            <van-tag v-if="order.tracking_status" :type="statusTagType(order.tracking_status)" size="medium">
              {{ order.tracking_status }}
            </van-tag>
            <span v-else>—</span>
          </template>
        </van-cell>
        <van-cell title="订单日期" :value="order.order_date || '—'" />
        <van-cell title="客户" :value="order.customer_name || '—'" />
        <van-cell title="订单金额(USD)" :value="fmtMoney(order.amount_usd)" />
        <van-cell title="运费" :value="fmtMoney(order.freight)" />
        <van-cell title="物流保险费" :value="fmtMoney(order.insurance)" />
        <van-cell title="附加费用" :value="fmtMoney(order.surcharge)" />
        <van-cell title="交易服务费(USD)" :value="fmtMoney(order.service_fee_usd)" />
        <van-cell title="运输成本" :value="fmtMoney(order.transport_cost)" />
        <van-cell title="承运商" :value="order.carrier || '—'" />
        <van-cell title="物流方式" :value="order.logistics_method || '—'" />
        <van-cell title="物流单号" :value="order.tracking_no || '—'" />
        <van-cell title="备注">
          <template #value>
            <span class="remark">{{ order.remark || '—' }}</span>
          </template>
        </van-cell>
        <van-cell title="订单毛利(USD)">
          <template #value>
            <span :class="profitClass(order.order_profit_usd)">{{ fmtMoney(order.order_profit_usd) }}</span>
          </template>
        </van-cell>
        <van-cell title="创建时间" :value="order.created_at || '—'" />
        <van-cell title="更新时间" :value="order.updated_at || '—'" />
      </van-cell-group>

      <van-cell-group inset title="产品明细" class="items-group">
        <van-empty v-if="!order.items || !order.items.length" description="暂无产品明细" />
        <van-cell
          v-for="(it, i) in order.items || []"
          :key="i"
          :title="`#${it.seq}  ${it.product_no}`"
          :label="`型号：${it.model || '—'}　规格：${it.spec || '—'}　数量：${it.qty}`"
          center
        >
          <template #value>
            <div class="item-value">
              <div>小计 <span class="amount">${{ fmtMoney(it.subtotal) }}</span></div>
              <div class="muted">单价 {{ fmtMoney(it.unit_price) }}</div>
              <div class="muted">成本 {{ fmtMoney(it.cost_price) }}</div>
              <div>毛利 <span :class="profitClass(it.profit_usd)">${{ fmtMoney(it.profit_usd) }}</span></div>
              <div class="muted">毛利率 {{ fmtRate(it.profit_rate) }}</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <div class="action-bar">
        <van-button block @click="router.back()">返回</van-button>
        <van-button v-if="canEdit" block type="primary" @click="router.push(`/m/orders/${route.params.id}/edit`)">
          编辑
        </van-button>
      </div>
    </template>

    <van-empty v-else description="订单加载失败" />
  </div>
</template>

<style scoped>
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.info-group,
.items-group {
  margin-top: 12px;
}
.remark {
  white-space: pre-wrap;
  word-break: break-all;
}
.item-value {
  text-align: right;
  font-size: 13px;
  line-height: 1.6;
}
.item-value .amount {
  color: #1989fa;
  font-weight: 600;
}
.item-value .muted {
  color: #969799;
}
.profit-positive {
  color: var(--van-success-color, #07c160);
}
.profit-negative {
  color: var(--van-danger-color, #ee0a24);
}
.action-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
}
</style>