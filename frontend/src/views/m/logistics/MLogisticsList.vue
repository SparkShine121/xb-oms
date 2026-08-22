<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listShipments } from '../../../api/logistics'
import { useUserStore } from '../../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
// 后端 LogisticsPermission：create/update 仅 tracker/admin
const canCreate = computed(() => roles.value.includes('admin') || roles.value.includes('tracker'))

// 与 PC LogisticsList 对齐的归属选项
const PAYER_OPTIONS = [
  { text: '客户', value: 'customer' },
  { text: '公司', value: 'company' },
  { text: '工厂', value: 'factory' },
]
const payerOptions = [{ text: '全部归属', value: '' }, ...PAYER_OPTIONS]

function payerLabel(p: string) {
  return PAYER_OPTIONS.find(o => o.value === p)?.text ?? p
}

function payerTagType(p: string) {
  if (p === 'customer') return 'primary'
  if (p === 'company') return 'success'
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
const payerFilter = ref<string>('')

async function onLoad() {
  try {
    const resp: any = await listShipments({
      page: page.value,
      page_size: pageSize,
      payer: payerFilter.value || undefined,
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
function onPayerChange() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function goEdit(id: number) {
  router.push(`/m/logistics/${id}/edit`)
}
</script>

<template>
  <div class="m-logistics-list">
    <van-nav-bar title="物流发货">
      <template v-if="canCreate" #right>
        <van-icon name="plus" size="20" @click="router.push('/m/logistics/new')" />
      </template>
    </van-nav-bar>

    <van-dropdown-menu>
      <van-dropdown-item v-model="payerFilter" :options="payerOptions" @change="onPayerChange" />
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
        @click="goEdit(item.id)"
      >
        <template #title>
          <div class="cell-title">
            <span class="order-no">{{ item.order_no }}</span>
            <span class="seq">#{{ item.seq }}</span>
            <van-tag :type="payerTagType(item.payer)" size="medium" plain>
              {{ payerLabel(item.payer) }}
            </van-tag>
          </div>
        </template>
        <template #label>
          <span class="cell-label">
            {{ item.carrier_name || '—' }} → {{ item.intl_name || '—' }} · {{ item.tracking_no || '无单号' }}
          </span>
        </template>
        <template #value>
          <span class="amount">{{ fmtMoney(item.cost) }} {{ item.cost_currency }}</span>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="finished && !rows.length" description="暂无物流发货数据" />
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
.seq {
  color: #969799;
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
