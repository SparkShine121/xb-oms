<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { getPayment, createRecord } from '../../../api/factoryPayment'
import { useUserStore } from '../../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const canManage = computed(() => roles.value.includes('admin') || roles.value.includes('finance'))

const payment = ref<any>(null)
const loading = ref(false)

// ---- 登记付款 ----
const showForm = ref(false)
const saving = ref(false)
const form = ref({ amount: '', payment_date: '', note: '' })
const showDatePicker = ref(false)
const datePickerValue = ref<string[]>([])

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
  } catch {
    // 错误提示由全局拦截器处理；payment 保持 null，下面渲染失败占位
    payment.value = null
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { amount: '', payment_date: today(), note: '' }
  showForm.value = true
}

function openDatePicker() {
  if (form.value.payment_date) {
    datePickerValue.value = form.value.payment_date.split('-')
  } else {
    datePickerValue.value = today().split('-')
  }
  showDatePicker.value = true
}

function onDateConfirm({ selectedValues }: { selectedValues: string[] }) {
  form.value.payment_date = selectedValues.join('-')
  showDatePicker.value = false
}

async function doCreate() {
  if (!form.value.amount || Number(form.value.amount) <= 0) {
    return showFailToast('请输入付款金额')
  }
  if (!form.value.payment_date) {
    return showFailToast('请选择付款日期')
  }
  saving.value = true
  try {
    await createRecord({
      factory_payment: payment.value.id,
      amount: Number(form.value.amount),
      payment_date: form.value.payment_date,
      note: form.value.note,
    })
    showSuccessToast('付款登记成功')
    showForm.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="m-factory-payment-detail">
    <van-nav-bar title="结算单详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" />
    </div>

    <template v-else-if="payment">
      <van-cell-group inset title="结算信息" class="info-group">
        <van-cell title="订单号" :value="payment.order_no" />
        <van-cell title="产品编号" :value="payment.product_no || '—'" />
        <van-cell title="工厂" :value="payment.factory_name || '—'" />
        <van-cell title="应付金额(CNY)">
          <template #value>
            <span class="amount">{{ fmtMoney(payment.amount_cny) }}</span>
          </template>
        </van-cell>
        <van-cell title="已付金额(CNY)">
          <template #value>
            <span class="paid">{{ fmtMoney(payment.paid_amount) }}</span>
          </template>
        </van-cell>
        <van-cell title="待付金额(CNY)">
          <template #value>
            <span class="unpaid">{{ unpaid() }}</span>
          </template>
        </van-cell>
        <van-cell title="状态">
          <template #value>
            <van-tag :type="statusTagType(payment.status)" size="medium">{{ payment.status }}</van-tag>
          </template>
        </van-cell>
        <van-cell title="备注">
          <template #value>
            <span class="remark">{{ payment.note || '—' }}</span>
          </template>
        </van-cell>
        <van-cell title="创建时间" :value="payment.created_at || '—'" />
        <van-cell title="更新时间" :value="payment.updated_at || '—'" />
      </van-cell-group>

      <van-cell-group inset title="付款记录" class="records-group">
        <van-empty v-if="!payment.records || !payment.records.length" description="暂无付款记录" />
        <van-cell v-for="r in payment.records || []" :key="r.id" :title="r.payment_date || '—'">
          <template #label>
            <span class="cell-label">{{ r.note || '—' }}</span>
          </template>
          <template #value>
            <span class="paid">¥{{ fmtMoney(r.amount) }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <div v-if="canManage" class="action-bar">
        <van-button block type="primary" @click="openCreate">登记付款</van-button>
      </div>
    </template>

    <!-- 登记付款弹窗 -->
    <van-popup v-model:show="showForm" position="bottom" round>
      <div class="form-title">登记付款</div>
      <van-form @submit="doCreate">
        <van-cell-group inset>
          <van-field v-model="form.amount" type="number" label="付款金额(CNY)" placeholder="0.00" />
          <van-field
            :model-value="form.payment_date"
            is-link
            readonly
            label="付款日期"
            placeholder="选择日期"
            @click="openDatePicker"
          />
          <van-field
            v-model="form.note"
            type="textarea"
            label="备注"
            placeholder="付款方式、凭证号等（选填）"
            rows="2"
            autosize
          />
        </van-cell-group>
        <div class="popup-actions">
          <van-button block @click="showForm = false" native-type="button">取消</van-button>
          <van-button block round type="primary" native-type="submit" :loading="saving">保存</van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 付款日期选择 -->
    <van-popup v-model:show="showDatePicker" position="bottom">
      <van-date-picker
        v-model="datePickerValue"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.info-group {
  margin-top: 12px;
}
.records-group {
  margin-top: 12px;
}
.remark {
  color: #646566;
}
.cell-label {
  color: #969799;
  font-size: 13px;
}
.amount {
  color: #1989fa;
  font-weight: 600;
}
.paid {
  color: #1989fa;
  font-weight: 600;
}
.unpaid {
  color: #ee0a24;
  font-weight: 600;
}
.action-bar {
  padding: 16px;
}
.form-title {
  padding: 16px 16px 0;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}
.popup-actions {
  display: flex;
  gap: 12px;
  padding: 12px 16px 24px;
}
</style>
