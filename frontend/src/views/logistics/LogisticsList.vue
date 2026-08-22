<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listShipments, deleteShipment } from '../../api/logistics'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
// 后端 LogisticsPermission：update 仅 tracker/admin，destroy 仅 admin
const canEdit = computed(() => roles.value.includes('admin') || roles.value.includes('tracker'))
const isAdmin = computed(() => roles.value.includes('admin'))

const PAYER_OPTIONS = [
  { value: 'customer', label: '客户' },
  { value: 'company', label: '公司' },
  { value: 'factory', label: '工厂' },
]

const CURRENCY_OPTIONS = ['CNY', 'USD']

function payerTagType(p: string) {
  if (p === 'customer') return 'primary'
  if (p === 'company') return 'success'
  return 'warning'
}

function payerLabel(p: string) {
  return PAYER_OPTIONS.find(o => o.value === p)?.label ?? p
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const search = ref('')
const payerFilter = ref<string | null>(null)
const currencyFilter = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const resp: any = await listShipments({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
      payer: payerFilter.value ?? undefined,
      cost_currency: currencyFilter.value ?? undefined,
    })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

function query() {
  page.value = 1
  load()
}

function goEdit(id: number) {
  router.push(`/logistics/${id}/edit`)
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除发货单「${row.order_no} #${row.seq}」？`, '删除确认', { type: 'warning' })
  await deleteShipment(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div class="logistics-list">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input
          v-model="search"
          placeholder="搜索物流单号 / 订单号"
          clearable
          style="width: 220px"
          @keyup.enter="query"
          @clear="query"
        />
        <el-select v-model="payerFilter" clearable placeholder="费用归属" style="width: 130px" @change="query">
          <el-option v-for="o in PAYER_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="currencyFilter" clearable placeholder="币种" style="width: 110px" @change="query">
          <el-option v-for="c in CURRENCY_OPTIONS" :key="c" :label="c" :value="c" />
        </el-select>
        <el-button type="primary" @click="query">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column label="订单号" min-width="140">
          <template #default="{ row }">
            <router-link :to="`/orders/${row.order}`" class="order-link">{{ row.order_no }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="seq" label="批次" width="70" align="center" />
        <el-table-column prop="carrier_name" label="国内承运商" min-width="120" show-overflow-tooltip />
        <el-table-column prop="intl_name" label="国际物流" min-width="120" show-overflow-tooltip />
        <el-table-column prop="tracking_no" label="物流单号" min-width="150" show-overflow-tooltip>
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
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit" link type="primary" size="small" @click="goEdit(row.id)">编辑</el-button>
            <el-button v-if="isAdmin" link type="danger" size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pager"
        @current-change="load"
        @size-change="query"
      />
    </el-card>
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
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
.order-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.order-link:hover {
  text-decoration: underline;
}
</style>
