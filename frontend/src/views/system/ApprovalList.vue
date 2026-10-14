<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listApprovals, approveRequest, rejectRequest , cleanupOrphans as cleanupOrphansApi } from '../../api/systemMgmt'
import { useUserStore } from '../../stores/user'
import PageHeader from '../../components/PageHeader.vue'
import { modelLabel } from '../../utils/modelNames'
import SearchToolbar from '../../components/SearchToolbar.vue'
import DataTable from '../../components/DataTable.vue'
import AppPagination from '../../components/AppPagination.vue'
import { PhListChecks } from '@phosphor-icons/vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.roles.includes('admin'))

const TYPE_OPTIONS = [
  { value: 'settlement', label: '工厂结算' },
  { value: 'payment', label: '工厂付款' },
  { value: 'order_change', label: '订单变更' },
  { value: 'logistics', label: '物流发货' },
]
const STATUS_OPTIONS = [
  { value: 'pending', label: '待审批' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
  { value: 'cancelled', label: '已关闭' }, // BUG-SIM-032：目标对象删除后自动/批量关闭
]

function typeLabel(v: string) {
  return TYPE_OPTIONS.find(o => o.value === v)?.label ?? v
}
function statusLabel(v: string) {
  return STATUS_OPTIONS.find(o => o.value === v)?.label ?? v
}
function statusTagType(v: string): 'warning' | 'success' | 'danger' | 'info' {
  if (v === 'pending') return 'warning'
  if (v === 'approved') return 'success'
  if (v === 'rejected') return 'danger'
  return 'info'  // cancelled
}

// BUG-SIM-032：批量关闭目标已删除的 pending 审批
async function cleanupOrphans() {
  await ElMessageBox.confirm('确定批量关闭所有目标对象已删除的待审批申请？', '清理孤儿审批', { type: 'warning' })
  const r: any = await cleanupOrphansApi()
  ElMessage.success(`已关闭 ${r.data?.closed ?? 0} 条孤儿审批`)
  load()
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const typeFilter = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const resp: any = await listApprovals({
      page: page.value,
      page_size: pageSize.value,
      approval_type: typeFilter.value || undefined,
      status: statusFilter.value || undefined,
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

async function doApprove(row: any) {
  await ElMessageBox.confirm(
    `通过「${typeLabel(row.approval_type)}」申请（${row.target_model}#${row.target_id}）？`,
    '审批确认', { type: 'warning' },
  )
  await approveRequest(row.id)
  ElMessage.success('已通过')
  load()
}

async function doReject(row: any) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因（可选）', '驳回申请', {
    inputType: 'textarea',
    confirmButtonText: '驳回',
    cancelButtonText: '取消',
  })
  await rejectRequest(row.id, value || '')
  ElMessage.success('已驳回')
  load()
}

onMounted(load)
</script>

<template>
  <div class="approval-list">
    <PageHeader title="待审批" />

    <DataTable
      :loading="loading"
      :data="rows"
      border
      stripe
      empty-title="没有待审批项"
      :empty-icon="PhListChecks"
    >
      <template #toolbar>
        <SearchToolbar>
          <template #filters>
            <el-select v-model="typeFilter" clearable placeholder="类型" style="width: 150px" @change="query">
              <el-option v-for="o in TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
            <el-button v-if="isAdmin" @click="cleanupOrphans">清理孤儿审批</el-button>
          <el-select v-model="statusFilter" clearable placeholder="状态" style="width: 130px" @change="query">
              <el-option v-for="o in STATUS_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
            <el-button type="primary" @click="query">查询</el-button>
          </template>
        </SearchToolbar>
      </template>

      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">{{ typeLabel(row.approval_type) }}</template>
      </el-table-column>
      <el-table-column label="目标对象" min-width="150">
        <template #default="{ row }">{{ modelLabel(row.target_model) }} #{{ row.target_id }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="submitted_by_name" label="提交人" width="110" />
      <el-table-column prop="reviewed_by_name" label="审批人" width="110" />
      <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column prop="created_at" label="申请时间" min-width="170">
        <template #default="{ row }">{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button link type="success" size="small" @click="doApprove(row)">通过</el-button>
            <el-button link type="danger" size="small" @click="doReject(row)">驳回</el-button>
          </template>
          <span v-else class="done-text">已处理</span>
        </template>
      </el-table-column>

      <template #footer>
        <AppPagination v-model:page="page" v-model:page-size="pageSize" :total="total" @change="load" />
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.done-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
