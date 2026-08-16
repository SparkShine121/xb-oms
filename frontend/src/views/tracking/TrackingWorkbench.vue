<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listMyOrders, advanceOrder, rejectOrder, getTimeline } from '../../api/tracking'

const STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款']

function statusTagType(s: string) {
  if (s === '签收' || s === '结算' || s === '回款') return 'success'
  if (s === '接单' || s === '排产') return 'info'
  return 'warning'
}

function fmtStay(seconds: number) {
  if (seconds == null || isNaN(seconds)) return '—'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`
  return `${Math.floor(seconds / 86400)}天${Math.floor((seconds % 86400) / 3600)}小时`
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const statusFilter = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const resp: any = await listMyOrders({
      page: page.value,
      page_size: pageSize.value,
      tracking_status: statusFilter.value ?? undefined,
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

// ---- 推进 / 驳回抽屉 ----
const drawerVisible = ref(false)
const drawerMode = ref<'advance' | 'reject'>('advance')
const currentOrder = ref<any>(null)
const note = ref('')
const fileList = ref<any[]>([])
const saving = ref(false)
const uploadRef = ref()

function openDrawer(row: any, mode: 'advance' | 'reject') {
  currentOrder.value = row
  drawerMode.value = mode
  note.value = ''
  fileList.value = []
  uploadRef.value?.clearFiles()
  drawerVisible.value = true
}

function onFileChange(uploadFile: any) {
  const f: File = uploadFile.raw
  if (!f) return
  if (!/^image\/(jpeg|png)$/.test(f.type)) {
    ElMessage.warning(`照片 ${f.name} 格式不支持（仅 jpg/png）`)
    uploadRef.value?.handleRemove(uploadFile)
    return
  }
  if (f.size > 5 * 1024 * 1024) {
    ElMessage.warning(`照片 ${f.name} 超过 5MB`)
    uploadRef.value?.handleRemove(uploadFile)
    return
  }
}

async function submit() {
  if (!currentOrder.value) return
  if (!note.value.trim()) return ElMessage.warning('请填写跟进说明')
  saving.value = true
  try {
    const photos = fileList.value.map((f: any) => f.raw).filter(Boolean)
    const data = { note: note.value.trim(), photos }
    if (drawerMode.value === 'advance') await advanceOrder(currentOrder.value.id, data)
    else await rejectOrder(currentOrder.value.id, data)
    ElMessage.success(drawerMode.value === 'advance' ? '已推进' : '已驳回')
    drawerVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

// ---- 时间线弹窗 ----
const timelineVisible = ref(false)
const timelineOrder = ref<any>(null)
const timelineLogs = ref<any[]>([])
const timelineLoading = ref(false)

async function openTimeline(row: any) {
  timelineOrder.value = row
  timelineVisible.value = true
  timelineLoading.value = true
  try {
    const resp: any = await getTimeline(row.id)
    timelineLogs.value = resp.data
  } finally {
    timelineLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="tracking-workbench">
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="statusFilter" clearable placeholder="跟踪状态" style="width: 140px" @change="query">
          <el-option v-for="s in STATUS_OPTIONS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="query">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column label="订单号" min-width="150">
          <template #default="{ row }">
            <router-link :to="`/orders/${row.id}`" class="order-link">{{ row.order_no }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="140" show-overflow-tooltip />
        <el-table-column label="跟踪状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.tracking_status)" size="small">{{ row.tracking_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前节点停留" width="140">
          <template #default="{ row }">{{ fmtStay(row.stay_seconds) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.can_advance" link type="primary" size="small" @click="openDrawer(row, 'advance')">
              推进
            </el-button>
            <el-button v-if="row.can_reject" link type="warning" size="small" @click="openDrawer(row, 'reject')">
              驳回
            </el-button>
            <el-button link type="info" size="small" @click="openTimeline(row)">时间线</el-button>
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

    <!-- 推进 / 驳回抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="(drawerMode === 'advance' ? '推进' : '驳回') + ' - ' + (currentOrder?.order_no ?? '')"
      size="480px"
    >
      <el-form label-position="top">
        <el-form-item label="跟进说明">
          <el-input
            v-model="note"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="填写跟进说明"
          />
        </el-form-item>
        <el-form-item label="照片（最多 9 张，jpg/png，单张 <5MB）">
          <el-upload
            ref="uploadRef"
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="9"
            accept=".jpg,.jpeg,.png"
            list-type="picture-card"
            :on-change="onFileChange"
            :on-exceed="() => ElMessage.warning('最多上传 9 张照片')"
          >
            <span class="upload-plus">+</span>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">确定</el-button>
      </template>
    </el-drawer>

    <!-- 时间线弹窗 -->
    <el-dialog v-model="timelineVisible" :title="'跟单时间线 - ' + (timelineOrder?.order_no ?? '')" width="640px">
      <div v-loading="timelineLoading" class="timeline-body">
        <el-empty v-if="!timelineLoading && !timelineLogs.length" description="暂无跟单记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="log in timelineLogs"
            :key="log.id"
            :timestamp="log.created_at"
            :type="log.is_reject ? 'danger' : 'primary'"
          >
            <div class="tl-head">
              <el-tag :type="log.is_reject ? 'danger' : statusTagType(log.node)" size="small">{{ log.node }}</el-tag>
              <el-tag v-if="log.is_reject" type="danger" size="small" effect="plain">驳回</el-tag>
              <span class="tl-operator">{{ log.operator_name }}</span>
            </div>
            <p v-if="log.note" class="tl-note">{{ log.note }}</p>
            <div v-if="log.photos?.length" class="tl-photos">
              <el-image
                v-for="(p, i) in log.photos"
                :key="p.id"
                :src="p.image_url"
                :preview-src-list="log.photos.map((x: any) => x.image_url)"
                :initial-index="i"
                fit="cover"
                class="tl-photo"
                preview-teleported
              />
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
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
.upload-plus {
  font-size: 24px;
  color: var(--el-text-color-secondary);
}
.timeline-body {
  min-height: 120px;
}
.tl-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tl-operator {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.tl-note {
  margin: 8px 0;
  font-size: 14px;
  white-space: pre-wrap;
}
.tl-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tl-photo {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
