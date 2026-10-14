<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listExchangeRates, createExchangeRate, updateExchangeRate, deleteExchangeRate } from '../../api/orders'
import { useUserStore } from '../../stores/user'
import PageHeader from '../../components/PageHeader.vue'
import DataTable from '../../components/DataTable.vue'
import AppPagination from '../../components/AppPagination.vue'

// BUG-SIM-022：汇率管理页（全员可读，admin 增删改；保存/删除后端自动重算受影响订单毛利）
const userStore = useUserStore()
const isAdmin = computed(() => userStore.roles.includes('admin'))

interface RateItem {
  id: number
  currency_pair: string
  rate: string
  effective_date: string
}

const rates = ref<RateItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ currency_pair: 'USD/CNY', rate: '' as string | number, effective_date: '' })

async function load() {
  loading.value = true
  try {
    const resp: any = await listExchangeRates({ page: page.value, page_size: pageSize.value })
    rates.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.currency_pair = 'USD/CNY'
  form.rate = ''
  form.effective_date = ''
  dialogVisible.value = true
}

function openEdit(r: RateItem) {
  editingId.value = r.id
  form.currency_pair = r.currency_pair
  form.rate = r.rate
  form.effective_date = r.effective_date
  dialogVisible.value = true
}

async function save() {
  if (!form.rate) return ElMessage.warning('请输入汇率')
  if (!form.effective_date) return ElMessage.warning('请选择生效日期')
  saving.value = true
  try {
    const payload = { currency_pair: form.currency_pair, rate: form.rate, effective_date: form.effective_date }
    if (editingId.value) {
      await updateExchangeRate(editingId.value, payload)
    } else {
      await createExchangeRate(payload)
    }
    ElMessage.success('保存成功，受影响订单毛利已自动重算')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(r: RateItem) {
  await ElMessageBox.confirm(
    `确定删除 ${r.currency_pair} @ ${r.effective_date}（${r.rate}）？删除后受影响订单毛利将回退至新的适用汇率`,
    '删除确认', { type: 'warning' })
  await deleteExchangeRate(r.id)
  ElMessage.success('已删除，受影响订单毛利已自动重算')
  load()
}

onMounted(load)
</script>

<template>
  <div class="rate-manage">
    <PageHeader title="汇率">
      <el-button v-if="isAdmin" type="primary" @click="openCreate">新增汇率</el-button>
    </PageHeader>

    <DataTable :loading="loading" :data="rates" border stripe empty-title="还没有汇率记录">
      <el-table-column prop="currency_pair" label="币种对" width="140" />
      <el-table-column prop="rate" label="汇率（1 USD = ? CNY）" min-width="160" />
      <el-table-column prop="effective_date" label="生效日期" width="140" />
      <el-table-column label="操作" v-if="isAdmin" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>

      <template #footer>
        <AppPagination v-model:page="page" v-model:page-size="pageSize" :total="total" @change="load" />
      </template>
    </DataTable>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑汇率' : '新增汇率'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="币种对">
          <el-input v-model="form.currency_pair" placeholder="USD/CNY" />
        </el-form-item>
        <el-form-item label="汇率" required>
          <el-input-number v-model="form.rate" :precision="4" :step="0.01" :min="0" :controls="false" style="width: 100%" />
        </el-form-item>
        <el-form-item label="生效日期" required>
          <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
