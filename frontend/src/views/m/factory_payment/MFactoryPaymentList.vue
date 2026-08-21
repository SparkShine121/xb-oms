<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listPayments } from '../../../api/factoryPayment'
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

const factoryFilter = ref<number>(0)
const factoryOptions = ref<{ text: string; value: number }[]>([])

async function onLoad() {
  try {
    const resp: any = await listPayments({
      page: page.value,
      page_size: pageSize,
      factory: factoryFilter.value || undefined,
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

async function loadFactories() {
  const resp: any = await listFactories({ page: 1, page_size: 200 })
  factoryOptions.value = [
    { text: '全部工厂', value: 0 },
    ...(resp.data.results ?? []).map((f: any) => ({ text: f.name, value: f.id })),
  ]
}

// 筛选切换：重置分页并重新加载
function onFactoryChange() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function goDetail(id: number) {
  router.push(`/m/factory-payment/${id}`)
}

onMounted(loadFactories)
</script>

<template>
  <div class="m-factory-payment-list">
    <van-nav-bar title="工厂结算">
      <template #right>
        <span class="statement-link" @click="router.push('/m/factory-payment/statement')">对账</span>
      </template>
    </van-nav-bar>

    <van-dropdown-menu>
      <van-dropdown-item v-model="factoryFilter" :options="factoryOptions" @change="onFactoryChange" />
    </van-dropdown-menu>

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
  </div>
</template>

<style scoped>
.statement-link {
  color: #1989fa;
  font-size: 14px;
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
