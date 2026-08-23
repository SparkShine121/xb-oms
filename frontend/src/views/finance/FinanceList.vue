<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listLedger, exportLedger } from '../../api/finance'
import PaymentInForm from './PaymentInForm.vue'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
// 后端 FinancePermission：create/update 仅 admin/finance
const canRegister = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))

const TYPE_OPTIONS = [
  { value: 'income_receipt', label: '回款收入' },
  { value: 'expense_factory', label: '工厂结算支出' },
  { value: 'expense_logistics', label: '物流费用支出' },
  { value: 'expense_service_fee', label: '服务费支出' },
]

function typeLabel(t: string) {
  return TYPE_OPTIONS.find(o => o.value === t)?.label ?? t
}

function typeTagType(t: string): 'success' | 'warning' | 'primary' | 'info' {
  if (t === 'income_receipt') return 'success'
  if (t === 'expense_factory') return 'warning'
  if (t === 'expense_logistics') return 'primary'
  return 'info'
}

function amountClass(a: any) {
  return Number(a) >= 0 ? 'amount-in' : 'amount-out'
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  const n = Number(v)
  return n >= 0 ? n.toFixed(2) : `-${Math.abs(n).toFixed(2)}`
}

const rows = ref<any[]>([])
const loading = ref(false)

const dateRange = ref<[string, string] | null>(null)
const typeFilter = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const resp: any = await listLedger({
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      type: typeFilter.value || undefined,
    })
    // ledger 为聚合接口，返回完整数组（非分页结构）
    rows.value = resp.data ?? []
  } finally {
    loading.value = false
  }
}

function query() {
  load()
}

async function doExport() {
  const blob: any = await exportLedger({
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1],
    type: typeFilter.value || undefined,
  })
  const url = URL.createObjectURL(blob as unknown as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '收支流水.xlsx'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

// ---- 回款登记弹窗 ----
const showForm = ref(false)
const presetOrderId = ref<number | null>(null)

function openRegister(orderId?: number | null) {
  presetOrderId.value = orderId ?? null
  showForm.value = true
}

onMounted(() => {
  // 从 OrderDetail「登记回款」跳入：/finance?register=1&order_id=X
  if (route.query.register) {
    openRegister(Number(route.query.order_id) || null)
  }
  load()
})
</script>

<template>
  <div class="finance-ledger">
    <el-card shadow="never">
      <div class="toolbar">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
          @change="query"
        />
        <el-select v-model="typeFilter" clearable placeholder="类型" style="width: 150px" @change="query">
          <el-option v-for="o in TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="query">查询</el-button>
        <el-button @click="doExport">导出 Excel</el-button>
        <el-button v-if="canRegister" type="success" class="register-btn" @click="openRegister()">
          登记回款
        </el-button>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.type)" size="small">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="amountClass(row.amount)">{{ fmtMoney(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="currency" label="币种" width="80" align="center" />
        <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
      </el-table>
    </el-card>

    <PaymentInForm v-model="showForm" :preset-order-id="presetOrderId" @saved="load" />
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.register-btn {
  margin-left: auto;
}
.amount-in {
  color: var(--el-color-success);
}
.amount-out {
  color: var(--el-color-danger);
}
</style>
