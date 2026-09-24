<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listLogs } from '../../api/systemMgmt'
import PageHeader from '../../components/PageHeader.vue'
import SearchToolbar from '../../components/SearchToolbar.vue'
import DataTable from '../../components/DataTable.vue'
import AppPagination from '../../components/AppPagination.vue'
import { PhClockCounterClockwise } from '@phosphor-icons/vue'

const ACTION_OPTIONS = [
  { value: 'POST', label: '新增' },
  { value: 'PUT', label: '更新' },
  { value: 'PATCH', label: '部分更新' },
  { value: 'DELETE', label: '删除' },
]

function actionLabel(v: string) {
  return ACTION_OPTIONS.find(o => o.value === v)?.label ?? v
}
function actionTagType(v: string): 'success' | 'warning' | 'primary' | 'danger' {
  if (v === 'POST') return 'success'
  if (v === 'PUT' || v === 'PATCH') return 'warning'
  if (v === 'DELETE') return 'danger'
  return 'primary'
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const actionFilter = ref<string | null>(null)
const search = ref('')
const dateRange = ref<[string, string] | null>(null)

async function load() {
  loading.value = true
  try {
    const resp: any = await listLogs({
      page: page.value,
      page_size: pageSize.value,
      action: actionFilter.value || undefined,
      search: search.value || undefined,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
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

onMounted(load)
</script>

<template>
  <div class="operation-log-list">
    <PageHeader title="操作日志" />

    <DataTable
      :loading="loading"
      :data="rows"
      border
      stripe
      empty-title="暂无日志"
      :empty-icon="PhClockCounterClockwise"
    >
      <template #toolbar>
        <SearchToolbar>
          <template #filters>
            <el-select v-model="actionFilter" clearable placeholder="操作类型" style="width: 130px" @change="query">
              <el-option v-for="o in ACTION_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
            <el-input
              v-model="search" clearable placeholder="搜索路径 / 用户名"
              style="width: 220px" @keyup.enter="query" @clear="query"
            />
            <el-date-picker
              v-model="dateRange" type="daterange" value-format="YYYY-MM-DD"
              range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
              style="width: 260px" @change="query"
            />
            <el-button type="primary" @click="query">查询</el-button>
          </template>
        </SearchToolbar>
      </template>

      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="created_at" label="时间" min-width="170">
        <template #default="{ row }">{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column prop="username" label="用户" width="130" />
      <el-table-column label="动作" width="110">
        <template #default="{ row }">
          <el-tag :type="actionTagType(row.action)" size="small">{{ actionLabel(row.action) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="path" label="请求路径" min-width="280" show-overflow-tooltip />

      <template #footer>
        <AppPagination v-model:page="page" v-model:page-size="pageSize" :total="total" @change="load" />
      </template>
    </DataTable>
  </div>
</template>
