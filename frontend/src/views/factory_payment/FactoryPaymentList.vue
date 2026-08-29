<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPayments, deletePayment, bulkDeletePayments } from '../../api/factoryPayment'
import { useBulkDelete } from '../../composables/useBulkDelete'
import { listFactories } from '../../api/basicInfo'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canManage = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))

const STATUS_OPTIONS = ['未结', '部分结', '已结']

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

const { selection, handleSelectionChange, handleBatchDelete } = useBulkDelete(bulkDeletePayments, load)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const factoryFilter = ref<number | null>(null)
const statusFilter = ref<string | null>(null)
const factories = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const resp: any = await listPayments({
      page: page.value,
      page_size: pageSize.value,
      factory: factoryFilter.value ?? undefined,
      status: statusFilter.value ?? undefined,
    })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

async function loadFactories() {
  const resp: any = await listFactories({ page: 1, page_size: 200 })
  factories.value = resp.data.results
}

async function remove(row: any) {
  await ElMessageBox.confirm(
    `确定删除结算单（订单 ${row.order_no} / ${row.product_no}）？删除后相关付款记录一并删除。`,
    '删除确认', { type: 'warning' },
  )
  await deletePayment(row.id)
  ElMessage.success('已删除')
  load()
}

function query() {
  page.value = 1
  load()
}

onMounted(() => { loadFactories(); load() })
</script>

<template>
  <div class="payment-list">
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="factoryFilter" clearable filterable placeholder="工厂" style="width: 200px" @change="query">
          <el-option v-for="f in factories" :key="f.id" :label="f.name" :value="f.id" />
        </el-select>
        <el-select v-model="statusFilter" clearable placeholder="结算状态" style="width: 130px" @change="query">
          <el-option v-for="s in STATUS_OPTIONS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="query">查询</el-button>
        <div class="toolbar-right">
          <el-button v-if="canManage" type="danger" plain :disabled="!selection.length" @click="handleBatchDelete">批量删除</el-button>
          <el-button @click="router.push('/factory-payment/statement')">对账单</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="order_no" label="订单号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="product_no" label="产品编号" width="120" show-overflow-tooltip />
        <el-table-column prop="factory_name" label="工厂" min-width="140" show-overflow-tooltip />
        <el-table-column label="应付(CNY)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.amount_cny) }}</template>
        </el-table-column>
        <el-table-column label="已付(CNY)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.paid_amount) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <router-link :to="`/factory-payment/${row.id}`" class="action-link">详情</router-link>
            <el-button v-if="canManage" link type="danger" size="small" @click="remove(row)">删除</el-button>
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
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
.action-link {
  color: var(--el-color-primary);
  text-decoration: none;
  margin-right: 8px;
  font-size: 13px;
}
.action-link:hover {
  text-decoration: underline;
}
</style>
