<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listOrders, deleteOrder, importOrders, downloadOrderTemplate, setTracker,
} from '../../api/orders'
import { listUsers } from '../../api/auth'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const isAdmin = computed(() => roles.value.includes('admin'))
const canImport = computed(() => isAdmin.value || roles.value.includes('salesman'))
const canCreate = computed(() => isAdmin.value || roles.value.includes('salesman'))
const canEdit = computed(() => isAdmin.value || roles.value.includes('salesman') || roles.value.includes('tracker'))

const STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款', '已取消']

function statusTagType(s: string) {
  if (s === '已取消') return 'danger'
  if (s === '签收' || s === '结算' || s === '回款') return 'success'
  if (s === '接单' || s === '排产') return 'info'
  return 'warning'
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

function profitClass(v: any) {
  const n = Number(v)
  if (isNaN(n)) return ''
  return n >= 0 ? 'profit-positive' : 'profit-negative'
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const search = ref('')
const statusFilter = ref<string | null>(null)
const salesmanFilter = ref<number | null>(null)
const trackerFilter = ref<number | null>(null)
const cancelledFilter = ref<string | null>(null)

const salesmen = ref<any[]>([])
const allUsers = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const resp: any = await listOrders({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
      tracking_status: statusFilter.value ?? undefined,
      salesman: salesmanFilter.value ?? undefined,
      tracker: trackerFilter.value ?? undefined,
      is_cancelled: cancelledFilter.value ?? undefined,
    })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  const resp: any = await listUsers({ page: 1, page_size: 200 })
  const all = resp.data.results
  allUsers.value = all
  salesmen.value = all.filter((u: any) => u.groups?.includes('salesman'))
}

function goEdit(id: number) {
  router.push(`/orders/${id}/edit`)
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除订单「${row.order_no}」？`, '删除确认', { type: 'warning' })
  await deleteOrder(row.id)
  ElMessage.success('已删除')
  load()
}

// ---- 派单（仅 admin） ----
const dispatchVisible = ref(false)
const dispatchOrder = ref<any>(null)
const dispatchTracker = ref<number | null>(null)
const dispatchSaving = ref(false)

function openDispatch(row: any) {
  dispatchOrder.value = row
  dispatchTracker.value = row.tracker ?? null
  dispatchVisible.value = true
}

async function doDispatch() {
  if (!dispatchTracker.value) return ElMessage.warning('请选择跟单员')
  dispatchSaving.value = true
  try {
    await setTracker(dispatchOrder.value.id, dispatchTracker.value)
    ElMessage.success('派单成功')
    dispatchVisible.value = false
    load()
  } finally {
    dispatchSaving.value = false
  }
}

// ---- 批量导入 / 模板下载 ----
const importFile = ref<File | null>(null)
const importResult = ref<any>(null)
const resultVisible = ref(false)

function onFileChange(uploadFile: any) {
  importFile.value = uploadFile.raw ?? null
}

async function doImport() {
  if (!importFile.value) return ElMessage.warning('请先选择 Excel 文件')
  const resp: any = await importOrders(importFile.value)
  importResult.value = resp.data
  resultVisible.value = true
  importFile.value = null
  load()
}

async function downloadTemplate() {
  const blob: Blob = (await downloadOrderTemplate()) as any
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'order_import_template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

function query() {
  page.value = 1
  load()
}

onMounted(() => { loadUsers(); load() })
</script>

<template>
  <div class="order-list">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input
          v-model="search"
          placeholder="搜索订单号 / 客户名"
          clearable
          style="width: 220px"
          @keyup.enter="query"
          @clear="query"
        />
        <el-select v-model="statusFilter" clearable placeholder="跟踪状态" style="width: 130px" @change="query">
          <el-option v-for="s in STATUS_OPTIONS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="salesmanFilter" clearable placeholder="业务员" style="width: 140px" @change="query">
          <el-option v-for="s in salesmen" :key="s.id" :label="s.username" :value="s.id" />
        </el-select>
        <el-select v-model="trackerFilter" clearable placeholder="跟单员" style="width: 140px" @change="query">
          <el-option v-for="u in allUsers" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
        <el-select v-model="cancelledFilter" clearable placeholder="订单状态" style="width: 120px" @change="query">
          <el-option label="正常" value="false" />
          <el-option label="已取消" value="true" />
        </el-select>
        <el-button type="primary" @click="query">查询</el-button>
        <div class="toolbar-right">
          <template v-if="canImport">
            <el-upload
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls"
              :on-change="onFileChange"
              :on-remove="() => (importFile = null)"
              :on-exceed="() => ElMessage.warning('仅支持导入 1 个文件')"
            >
              <el-button>选择 Excel</el-button>
            </el-upload>
            <el-button type="primary" plain :disabled="!importFile" @click="doImport">批量导入</el-button>
          </template>
          <el-button @click="downloadTemplate">下载模板</el-button>
          <el-button v-if="canCreate" type="primary" @click="router.push('/orders/new')">新增订单</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column label="订单号" min-width="140">
          <template #default="{ row }">
            <router-link :to="`/orders/${row.id}`" class="order-link">{{ row.order_no }}</router-link>
          </template>
        </el-table-column>
        <el-table-column label="跟踪状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.tracking_status" :type="statusTagType(row.tracking_status)" size="small">
              {{ row.tracking_status }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="order_date" label="订单日期" width="120" />
        <el-table-column prop="customer_name" label="客户" min-width="140" show-overflow-tooltip />
        <el-table-column label="金额(USD)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.amount_usd) }}</template>
        </el-table-column>
        <el-table-column prop="salesman_name" label="业务员" width="100" />
        <el-table-column prop="tracker_name" label="跟单员" width="100" />
        <el-table-column label="毛利(USD)" width="120" align="right">
          <template #default="{ row }">
            <span :class="profitClass(row.order_profit_usd)">{{ fmtMoney(row.order_profit_usd) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <router-link :to="`/orders/${row.id}`" class="action-link">详情</router-link>
            <el-button v-if="canEdit" link type="primary" size="small" @click="goEdit(row.id)">编辑</el-button>
            <el-button v-if="isAdmin" link type="warning" size="small" @click="openDispatch(row)">派单</el-button>
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

    <!-- 派单弹窗 -->
    <el-dialog v-model="dispatchVisible" title="派单 - 指定跟单员" width="420px">
      <p v-if="dispatchOrder" style="margin-bottom: 12px">
        订单：<strong>{{ dispatchOrder.order_no }}</strong>
      </p>
      <el-select v-model="dispatchTracker" placeholder="选择跟单员" style="width: 100%">
        <el-option v-for="u in allUsers" :key="u.id" :label="u.username" :value="u.id" />
      </el-select>
      <template #footer>
        <el-button @click="dispatchVisible = false">取消</el-button>
        <el-button type="primary" :loading="dispatchSaving" @click="doDispatch">确定</el-button>
      </template>
    </el-dialog>

    <!-- 导入结果弹窗 -->
    <el-dialog v-model="resultVisible" title="批量导入结果" width="560px">
      <template v-if="importResult">
        <p>成功 {{ importResult.success_count }} 条，失败 {{ importResult.fail_count }} 条</p>
        <div v-if="importResult.unmatched" class="unmatched">
          <p v-if="importResult.unmatched.customers?.length" class="unmatched-item">
            未匹配客户：{{ importResult.unmatched.customers.map((c: any) => c.name).join('、') }}
          </p>
          <p v-if="importResult.unmatched.products?.length" class="unmatched-item">
            未匹配产品：{{ importResult.unmatched.products.map((p: any) => p.product_no).join('、') }}
          </p>
          <p v-if="importResult.unmatched.factories?.length" class="unmatched-item">
            未匹配工厂：{{ importResult.unmatched.factories.map((f: any) => f.name).join('、') }}
          </p>
        </div>
        <el-table
          v-if="importResult.failures?.length"
          :data="importResult.failures"
          size="small"
          max-height="260"
          style="margin-top: 12px"
        >
          <el-table-column prop="row" label="行号" width="70" />
          <el-table-column prop="reason" label="失败原因" />
        </el-table>
      </template>
      <template #footer>
        <el-button type="primary" @click="resultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
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
.order-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.order-link:hover {
  text-decoration: underline;
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
.profit-positive {
  color: var(--el-color-success);
}
.profit-negative {
  color: var(--el-color-danger);
}
.unmatched {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}
.unmatched-item {
  margin: 4px 0;
  font-size: 13px;
  color: var(--el-color-warning);
}
</style>