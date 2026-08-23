<script setup lang="ts">
import { ref } from 'vue'
import { listLedger } from '../../api/finance'

const TYPE_OPTIONS = [
  { text: '全部类型', value: '' },
  { text: '回款收入', value: 'income_receipt' },
  { text: '工厂结算支出', value: 'expense_factory' },
  { text: '物流费用支出', value: 'expense_logistics' },
  { text: '服务费支出', value: 'expense_service_fee' },
]

function typeLabel(t: string) {
  return TYPE_OPTIONS.find(o => o.value === t)?.text ?? t
}

function typeTagType(t: string): 'success' | 'warning' | 'primary' | 'default' {
  if (t === 'income_receipt') return 'success'
  if (t === 'expense_factory') return 'warning'
  if (t === 'expense_logistics') return 'primary'
  return 'default'
}

function fmtAmount(v: any) {
  const n = Number(v)
  return n >= 0 ? `+${n.toFixed(2)}` : `-${Math.abs(n).toFixed(2)}`
}

const rows = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const typeFilter = ref('')

// ledger 为聚合接口，一次返回全量（非分页），van-list 仅做加载态
async function onLoad() {
  try {
    const resp: any = await listLedger({
      type: typeFilter.value || undefined,
    })
    rows.value = resp.data ?? []
    finished.value = true
  } catch {
    // 加载失败停止自动重试（错误提示由全局拦截器处理）
    finished.value = true
  } finally {
    loading.value = false
  }
}

function onTypeChange() {
  rows.value = []
  finished.value = false
  loading.value = true
  onLoad()
}
</script>

<template>
  <div class="m-finance-ledger">
    <van-nav-bar title="收支流水" />

    <van-dropdown-menu>
      <van-dropdown-item v-model="typeFilter" :options="TYPE_OPTIONS" @change="onTypeChange" />
    </van-dropdown-menu>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      finished-text="没有更多了"
      @load="onLoad"
    >
      <van-cell v-for="(item, i) in rows" :key="i" center>
        <template #title>
          <div class="cell-title">
            <span class="desc">{{ item.description }}</span>
          </div>
        </template>
        <template #label>
          <div class="cell-label">
            <span>{{ item.date }}</span>
            <van-tag :type="typeTagType(item.type)" size="medium" plain style="margin-left: 6px">
              {{ typeLabel(item.type) }}
            </van-tag>
          </div>
        </template>
        <template #value>
          <span class="amount" :class="Number(item.amount) >= 0 ? 'in' : 'out'">
            {{ fmtAmount(item.amount) }} {{ item.currency }}
          </span>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="finished && !rows.length" description="暂无收支流水" />
  </div>
</template>

<style scoped>
.cell-title {
  display: flex;
  align-items: center;
}
.desc {
  font-weight: 600;
  color: #323233;
}
.cell-label {
  display: flex;
  align-items: center;
  color: #969799;
  font-size: 13px;
}
.amount {
  font-weight: 600;
}
.amount.in {
  color: #07c160;
}
.amount.out {
  color: #ee0a24;
}
</style>
