<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showImagePreview, showSuccessToast, showFailToast } from 'vant'
import { listMyOrders, advanceOrder, rejectOrder, getTimeline } from '../../../api/tracking'

const router = useRouter()

const STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款']
const statusOptions = [{ text: '全部状态', value: '' }, ...STATUS_OPTIONS.map(s => ({ text: s, value: s }))]

function statusTagType(s: string) {
  if (s === '签收' || s === '结算' || s === '回款') return 'success'
  if (s === '接单' || s === '排产') return 'primary'
  return 'warning'
}

function fmtStay(seconds: number) {
  if (seconds == null || isNaN(seconds)) return '—'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`
  return `${Math.floor(seconds / 86400)}天${Math.floor((seconds % 86400) / 3600)}小时`
}

// ---- 列表 ----
const rows = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 20
const statusFilter = ref<string>('')

async function onLoad() {
  try {
    const resp: any = await listMyOrders({
      page: page.value,
      page_size: pageSize,
      tracking_status: statusFilter.value || undefined,
    })
    const data = resp.data
    rows.value = rows.value.concat(data.results)
    if (rows.value.length >= data.count) finished.value = true
    else page.value += 1
  } catch {
    // 加载失败停止自动重试（错误提示由全局拦截器处理）
    finished.value = true
  } finally {
    loading.value = false
  }
}

function onStatusChange() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function reload() {
  rows.value = []
  page.value = 1
  finished.value = false
  loading.value = true
  onLoad()
}

function goDetail(id: number) {
  router.push(`/m/orders/${id}`)
}

// ---- 推进 / 驳回表单 ----
const actionVisible = ref(false)
const actionMode = ref<'advance' | 'reject'>('advance')
const currentOrder = ref<any>(null)
const note = ref('')
const fileList = ref<any[]>([])
const saving = ref(false)

function openAction(row: any, mode: 'advance' | 'reject') {
  currentOrder.value = row
  actionMode.value = mode
  note.value = ''
  fileList.value = []
  actionVisible.value = true
}

function beforeRead(file: File | File[]) {
  const files = Array.isArray(file) ? file : [file]
  for (const f of files) {
    if (!/^image\/(jpeg|png)$/.test(f.type)) {
      showFailToast(`照片 ${f.name} 格式不支持（仅 jpg/png）`)
      return false
    }
    if (f.size > 5 * 1024 * 1024) {
      showFailToast(`照片 ${f.name} 超过 5MB`)
      return false
    }
  }
  return true
}

async function submit() {
  if (!currentOrder.value) return
  saving.value = true
  try {
    const photos = fileList.value.map((f: any) => f.file).filter(Boolean)
    const data = { note: note.value.trim(), photos }
    if (actionMode.value === 'advance') await advanceOrder(currentOrder.value.id, data)
    else await rejectOrder(currentOrder.value.id, data)
    showSuccessToast(actionMode.value === 'advance' ? '已推进' : '已驳回')
    actionVisible.value = false
    reload()
  } finally {
    saving.value = false
  }
}

// ---- 时间线 ----
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

function previewPhotos(log: any, index: string | number) {
  showImagePreview(log.photos.map((p: any) => p.image_url), Number(index))
}
</script>

<template>
  <div class="m-tracking-workbench">
    <van-nav-bar title="跟单工作台" />

    <van-dropdown-menu>
      <van-dropdown-item v-model="statusFilter" :options="statusOptions" @change="onStatusChange" />
    </van-dropdown-menu>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="rows.length ? '没有更多了' : ''"
      @load="onLoad"
    >
      <van-cell v-for="item in rows" :key="item.id" center>
        <template #title>
          <div class="cell-title" @click="goDetail(item.id)">
            <span class="order-no">{{ item.order_no }}</span>
            <van-tag v-if="item.tracking_status" :type="statusTagType(item.tracking_status)" size="medium" plain>
              {{ item.tracking_status }}
            </van-tag>
          </div>
        </template>
        <template #label>
          <div class="cell-label">
            <span>{{ item.customer_name || '—' }}</span>
            <span class="stay">当前节点停留 {{ fmtStay(item.stay_seconds) }}</span>
          </div>
        </template>
        <template #value>
          <div class="cell-actions">
            <van-button
              v-if="item.can_advance"
              size="mini"
              type="primary"
              plain
              @click.stop="openAction(item, 'advance')"
            >
              推进
            </van-button>
            <van-button
              v-if="item.can_reject"
              size="mini"
              type="warning"
              plain
              @click.stop="openAction(item, 'reject')"
            >
              驳回
            </van-button>
            <van-button size="mini" plain @click.stop="openTimeline(item)">时间线</van-button>
          </div>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="finished && !rows.length" description="暂无派给自己的订单" />

    <!-- 推进 / 驳回表单 -->
    <van-popup v-model:show="actionVisible" position="bottom" round>
      <div class="popup-header">
        {{ actionMode === 'advance' ? '推进' : '驳回' }} - {{ currentOrder?.order_no ?? '' }}
      </div>
      <van-form @submit="submit">
        <van-cell-group inset>
          <van-field
            v-model="note"
            name="note"
            label="跟进说明"
            type="textarea"
            rows="3"
            autosize
            maxlength="500"
            show-word-limit
            required
            :rules="[{ required: true, message: '请填写跟进说明' }]"
            placeholder="填写跟进说明"
          />
          <van-field name="photos" label="照片">
            <template #input>
              <van-uploader
                v-model="fileList"
                :max-count="9"
                multiple
                accept="image/jpeg,image/png"
                :before-read="beforeRead"
              />
            </template>
          </van-field>
        </van-cell-group>
        <div class="action-bar">
          <van-button block @click="actionVisible = false" native-type="button">取消</van-button>
          <van-button block type="primary" native-type="submit" :loading="saving">确定</van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 时间线 -->
    <van-popup v-model:show="timelineVisible" position="bottom" round class="tl-popup">
      <div class="popup-header">跟单时间线 - {{ timelineOrder?.order_no ?? '' }}</div>
      <div v-if="timelineLoading" class="loading-wrap">
        <van-loading type="spinner" />
      </div>
      <van-empty v-else-if="!timelineLogs.length" description="暂无跟单记录" />
      <van-cell-group v-else inset>
        <van-cell v-for="log in timelineLogs" :key="log.id" class="tl-cell">
          <template #title>
            <div class="tl-head">
              <van-tag :type="log.is_reject ? 'danger' : statusTagType(log.node)" size="medium">
                {{ log.node }}
              </van-tag>
              <van-tag v-if="log.is_reject" type="danger" size="medium" plain>驳回</van-tag>
              <span class="tl-operator">{{ log.operator_name }}</span>
            </div>
          </template>
          <template #label>
            <div class="tl-body">
              <div class="tl-time">{{ log.created_at }}</div>
              <p v-if="log.note" class="tl-note">{{ log.note }}</p>
              <div v-if="log.photos?.length" class="tl-photos">
                <van-image
                  v-for="(p, i) in log.photos"
                  :key="p.id"
                  :src="p.image_url"
                  fit="cover"
                  class="tl-photo"
                  @click="previewPhotos(log, i)"
                />
              </div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </van-popup>
  </div>
</template>

<style scoped>
.m-tracking-workbench {
  min-height: 100vh;
  background: #f7f8fa;
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
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #969799;
  font-size: 13px;
}
.stay {
  font-size: 12px;
}
.cell-actions {
  display: flex;
  gap: 6px;
}
.popup-header {
  padding: 16px 16px 8px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}
.action-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.tl-popup {
  max-height: 80vh;
  overflow-y: auto;
}
.tl-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tl-operator {
  font-size: 13px;
  color: #969799;
}
.tl-body {
  width: 100%;
}
.tl-time {
  font-size: 12px;
  color: #969799;
}
.tl-note {
  margin: 8px 0;
  font-size: 14px;
  color: #323233;
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
  overflow: hidden;
}
</style>
