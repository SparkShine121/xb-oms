<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listBackups, manualBackup, downloadBackup } from '../../api/systemMgmt'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const backingUp = ref(false)

function fileName(p: string) {
  return p ? p.split(/[\\/]/).pop() : ''
}

function fmtSize(n: number) {
  if (n >= 1024 * 1024) return (n / 1024 / 1024).toFixed(2) + ' MB'
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB'
  return n + ' B'
}

function triggerLabel(v: string) {
  return v === 'approval' ? '审批自动' : v === 'manual' ? '手动' : v
}
function triggerTagType(v: string): 'warning' | 'primary' {
  return v === 'approval' ? 'warning' : 'primary'
}

async function load() {
  loading.value = true
  try {
    const resp: any = await listBackups({ page: page.value, page_size: pageSize.value })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

async function doBackup() {
  await ElMessageBox.confirm('立即创建一次数据库备份？', '手动备份', { type: 'info' })
  backingUp.value = true
  try {
    await manualBackup()
    ElMessage.success('备份完成')
    load()
  } finally {
    backingUp.value = false
  }
}

async function doDownload(row: any) {
  const blob: any = await downloadBackup(row.id)
  const url = URL.createObjectURL(blob as unknown as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName(row.file_path) || `backup_${row.id}.db`
  a.click()
  URL.revokeObjectURL(url)
}

function onPageChange(p: number) {
  page.value = p
  load()
}

onMounted(load)
</script>

<template>
  <div class="backup-manage">
    <el-card shadow="never">
      <div class="toolbar">
        <el-button type="primary" :loading="backingUp" @click="doBackup">手动备份</el-button>
        <span class="tip">系统滚动保留最近 1000 份备份</span>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="文件名" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ fileName(row.file_path) }}</template>
        </el-table-column>
        <el-table-column label="大小" width="110" align="right">
          <template #default="{ row }">{{ fmtSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="触发方式" width="110">
          <template #default="{ row }">
            <el-tag :type="triggerTagType(row.trigger)" size="small">{{ triggerLabel(row.trigger) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="备份时间" min-width="170">
          <template #default="{ row }">{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="doDownload(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background layout="total, prev, pager, next"
          :total="total" :page-size="pageSize" :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
