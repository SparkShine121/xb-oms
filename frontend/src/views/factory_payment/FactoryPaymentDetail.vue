<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPayment, createRecord, deleteRecord } from '../../api/factoryPayment'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canManage = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))

const payment = ref<any>(null)
const loading = ref(false)

// ---- 登记付款 ----
const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({ amount: null as number | null, payment_date: '', note: '' })

function statusTagType(s: string) {
  if (s === '已结') return 'success'
  if (s === '部分结') return 'warning'
  return 'danger'
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

function unpaid() {
  if (!payment.value) return '—'
  return fmtMoney(Number(payment.value.amount_cny) - Number(payment.value.paid_amount))
}

function today() {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

async function load() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const resp: any = await getPayment(id)
    payment.value = resp.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { amount: null, payment_date: today(), note: '' }
  dialogVisible.value = true
}

async function doCreate() {
  if (form.value.amount == null || Number(form.value.amount) <= 0) {
    return ElMessage.warning('请输入付款金额')
  }
  if (!form.value.payment_date) return ElMessage.warning('请选择付款日期')
  saving.value = true
  try {
    await createRecord({
      factory_payment: payment.value.id,
      amount: Number(form.value.amount),
      payment_date: form.value.payment_date,
      note: form.value.note,
    })
    ElMessage.success('付款登记成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function removeRecord(row: any) {
  await ElMessageBox.confirm(
    `确定删除这笔付款记录（${fmtMoney(row.amount)} 元，${row.payment_date}）？`,
    '删除确认', { type: 'warning' },
  )
  await deleteRecord(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div class="payment-detail" v-loading="loading">
    <div class="detail-header">
      <el-button @click="router.push('/factory-payment')">返回列表</el-button>
    </div>

    <el-card v-if="payment" shadow="never">
      <template #header>
        <div class="card-header">
          <span>结算单详情 - {{ payment.order_no }} / {{ payment.product_no }}</span>
          <el-tag :type="statusTagType(payment.status)" size="small">{{ payment.status }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="订单号">{{ payment.order_no }}</el-descriptions-item>
        <el-descriptions-item label="产品编号">{{ payment.product_no }}</el-descriptions-item>
        <el-descriptions-item label="工厂">{{ payment.factory_name }}</el-descriptions-item>
        <el-descriptions-item label="应付金额(CNY)">{{ fmtMoney(payment.amount_cny) }}</el-descriptions-item>
        <el-descriptions-item label="已付金额(CNY)">{{ fmtMoney(payment.paid_amount) }}</el-descriptions-item>
        <el-descriptions-item label="待付金额(CNY)">{{ unpaid() }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ payment.created_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ payment.updated_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ payment.note || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="payment" shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>付款记录</span>
          <el-button v-if="canManage" type="primary" size="small" @click="openCreate">登记付款</el-button>
        </div>
      </template>
      <el-table :data="payment.records" border stripe size="small">
        <el-table-column label="付款日期" width="130">
          <template #default="{ row }">{{ row.payment_date }}</template>
        </el-table-column>
        <el-table-column label="金额(CNY)" width="140" align="right">
          <template #default="{ row }">{{ fmtMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.note || '—' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="登记时间" width="170" />
        <el-table-column v-if="canManage" label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="removeRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 登记付款弹窗 -->
    <el-dialog v-model="dialogVisible" title="登记付款" width="480px">
      <el-form label-width="90px">
        <el-form-item label="付款金额">
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" :step="100" style="width: 100%" placeholder="请输入付款金额(CNY)" />
        </el-form-item>
        <el-form-item label="付款日期">
          <el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" placeholder="选择付款日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" placeholder="付款方式、凭证号等（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
