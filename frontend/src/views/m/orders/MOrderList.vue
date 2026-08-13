<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listOrders } from '../../../api/orders'
import { useUserStore } from '../../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canCreate = computed(() => roles.value.includes('admin') || roles.value.includes('salesman'))

// 与 PC OrderList 对齐的状态选项
const STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款', '已取消']
const statusOptions = [{ text: '全部状态', value: '' }, ...STATUS_OPTIONS.map(s => ({ text: s, value: s }))]

function statusTagType(s: string) {
  if (s === '已取消') return 'danger'
  if (s === '签收' || s === '结算' || s === '回款') return 'success'
  if (s === '接单' || s === '排产') return 'primary'
  return 'warning'
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
const statusFilter = ref<string>('')

async function onLoad() {
  try {
    const resp: any = await listOrders({
      page: page.value,
      page_size: pageSize,
      tracking_status: statusFilter.value || undefined,
    })
    const data = resp.data
    rows.value = rows.value.concat(data.results)
    if (data.next) page.value += 1
    else finished.value = true
  } catch {
    // 加载失败停止自动重试（错误提示由全局拦截器处理）
    finished.value = true
  } finally {
    loading.value = false
  }
}

// 筛选切换：重置分页并重新加载
function onStatusChange() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function goDetail(id: number) {
  router.push(`/m/orders/${id}`)
}
</script>

<template>
  <div class="m-order-list">
    <van-nav-bar title="订单">
      <template v-if="canCreate" #right>
        <van-icon name="plus" size="20" @click="router.push('/m/orders/new')" />
      </template>
    </van-nav-bar>

    <van-dropdown-menu>
      <van-dropdown-item v-model="statusFilter" :options="statusOptions" @change="onStatusChange" />
    </van-dropdown-menu>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="rows.length ? '没有更多了' : ''"
      @load="onLoad"
    >
      <van-cell
        v-for="item in rows"
        :key="item.id"
        is-link
        center
        @click="goDetail(item.id)"
      >
        <template #title>
          <div class="cell-title">
            <span class="order-no">{{ item.order_no }}</span>
            <van-tag v-if="item.tracking_status" :type="statusTagType(item.tracking_status)" size="medium" plain>
              {{ item.tracking_status }}
            </van-tag>
          </div>
        </template>
        <template #label>
          <span class="cell-label">{{ item.customer_name || '—' }} · {{ item.order_date || '—' }}</span>
        </template>
        <template #value>
          <span class="amount">${{ fmtMoney(item.amount_usd) }}</span>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="finished && !rows.length" description="暂无订单数据" />
  </div>
</template>

<style scoped>
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
.amount {
  color: #1989fa;
  font-weight: 600;
}
</style>