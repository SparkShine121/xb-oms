<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getShipment, createShipment, updateShipment } from '../../../api/logistics'
import { listOrders } from '../../../api/orders'
import { listLogistics } from '../../../api/basicInfo'
import { showFailToast } from 'vant'

const props = defineProps<{ id?: string | number }>()
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!props.id)

const form = reactive({
  order: null as number | null,
  domestic_carrier: null as number | null,
  intl_method: null as number | null,
  tracking_no: '',
  cost: 0 as number | string,
  cost_currency: 'CNY',
  payer: 'company',
  note: '',
})

// 与 PC LogisticsForm 对齐的选项
const currencyColumns = [
  { text: '人民币', value: 'CNY' },
  { text: '美元', value: 'USD' },
]
const payerColumns = [
  { text: '客户', value: 'customer' },
  { text: '公司', value: 'company' },
  { text: '工厂', value: 'factory' },
]

const orders = ref<any[]>([])
const domesticCarriers = ref<any[]>([])
const intlMethods = ref<any[]>([])

const saving = ref(false)
const loading = ref(false)

// Picker 弹窗显示状态
const showOrderPicker = ref(false)
const showDomesticPicker = ref(false)
const showIntlPicker = ref(false)
const showCurrencyPicker = ref(false)
const showPayerPicker = ref(false)

// Picker 列数据
const orderColumns = computed(() => orders.value.map((o: any) => ({ text: o.order_no, value: o.id })))
const domesticColumns = computed(() => domesticCarriers.value.map((p: any) => ({ text: p.name, value: p.id })))
const intlColumns = computed(() => intlMethods.value.map((p: any) => ({ text: p.name, value: p.id })))

// Picker 字段显示文本
const orderText = computed(() => orders.value.find((o: any) => o.id === form.order)?.order_no || '')
const domesticText = computed(() => domesticCarriers.value.find((p: any) => p.id === form.domestic_carrier)?.name || '')
const intlText = computed(() => intlMethods.value.find((p: any) => p.id === form.intl_method)?.name || '')
const currencyText = computed(() => currencyColumns.find(c => c.value === form.cost_currency)?.text || '')
const payerText = computed(() => payerColumns.find(o => o.value === form.payer)?.text || '')

async function loadOptions() {
  const [orderResp, domesticResp, intlResp] = await Promise.all([
    listOrders({ page: 1, page_size: 200 }),
    listLogistics({ type: 'domestic', page: 1, page_size: 200 }),
    listLogistics({ type: 'international', page: 1, page_size: 200 }),
  ])
  orders.value = (orderResp as any).data.results ?? []
  domesticCarriers.value = (domesticResp as any).data.results ?? []
  intlMethods.value = (intlResp as any).data.results ?? []
}

async function loadShipment() {
  if (!props.id) return
  loading.value = true
  try {
    const resp: any = await getShipment(Number(props.id))
    const d = resp.data
    Object.assign(form, {
      order: d.order ?? null,
      domestic_carrier: d.domestic_carrier ?? null,
      intl_method: d.intl_method ?? null,
      tracking_no: d.tracking_no ?? '',
      cost: Number(d.cost) || 0,
      cost_currency: d.cost_currency ?? 'CNY',
      payer: d.payer ?? 'company',
      note: d.note ?? '',
    })
  } finally {
    loading.value = false
  }
}

function onOrderConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.order = v != null ? Number(v) : null
  showOrderPicker.value = false
}

function onDomesticConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.domestic_carrier = v != null ? Number(v) : null
  showDomesticPicker.value = false
}

function onIntlConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.intl_method = v != null ? Number(v) : null
  showIntlPicker.value = false
}

function onCurrencyConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.cost_currency = v != null ? String(v) : 'CNY'
  showCurrencyPicker.value = false
}

function onPayerConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.payer = v != null ? String(v) : 'company'
  showPayerPicker.value = false
}

async function onSubmit() {
  if (!form.order) {
    showFailToast('请选择订单')
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form,
      cost: Number(form.cost) || 0,
    }
    if (isEdit.value) await updateShipment(Number(props.id), payload)
    else await createShipment(payload)
    router.push('/m/logistics')
  } finally {
    saving.value = false
  }
}

function cancel() {
  router.back()
}

onMounted(async () => {
  await loadOptions()
  // 从订单详情「登记发货」跳入时预选订单
  const preOrderId = Number(route.query.order_id)
  if (!isEdit.value && preOrderId) form.order = preOrderId
  await loadShipment()
})
</script>

<template>
  <div class="m-logistics-form">
    <van-nav-bar :title="isEdit ? '编辑发货单' : '登记发货'" left-arrow @click-left="cancel" />

    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" />
    </div>

    <van-form v-else @submit="onSubmit">
      <van-cell-group inset title="发货信息">
        <van-field
          :model-value="orderText"
          is-link
          readonly
          required
          label="订单"
          placeholder="选择订单"
          @click="showOrderPicker = true"
        />
        <van-field
          :model-value="domesticText"
          is-link
          readonly
          label="国内承运商"
          placeholder="选择国内承运商"
          @click="showDomesticPicker = true"
        />
        <van-field
          :model-value="intlText"
          is-link
          readonly
          label="国际物流"
          placeholder="选择国际物流方式"
          @click="showIntlPicker = true"
        />
        <van-field
          v-model="form.tracking_no"
          name="tracking_no"
          label="物流单号"
          placeholder="物流单号"
        />
        <van-field
          v-model="form.cost"
          type="number"
          name="cost"
          label="费用"
          placeholder="0.00"
        />
        <van-field
          :model-value="currencyText"
          is-link
          readonly
          label="币种"
          placeholder="选择币种"
          @click="showCurrencyPicker = true"
        />
        <van-field
          :model-value="payerText"
          is-link
          readonly
          label="费用归属"
          placeholder="选择费用归属"
          @click="showPayerPicker = true"
        />
        <van-field
          v-model="form.note"
          type="textarea"
          label="备注"
          placeholder="备注"
          rows="2"
          autosize
        />
      </van-cell-group>

      <div class="action-bar">
        <van-button block @click="cancel" native-type="button">取消</van-button>
        <van-button block type="primary" native-type="submit" :loading="saving">保存</van-button>
      </div>
    </van-form>

    <!-- 订单选择 -->
    <van-popup v-model:show="showOrderPicker" position="bottom">
      <van-picker
        :columns="orderColumns"
        @confirm="onOrderConfirm"
        @cancel="showOrderPicker = false"
      />
    </van-popup>

    <!-- 国内承运商选择 -->
    <van-popup v-model:show="showDomesticPicker" position="bottom">
      <van-picker
        :columns="domesticColumns"
        @confirm="onDomesticConfirm"
        @cancel="showDomesticPicker = false"
      />
    </van-popup>

    <!-- 国际物流选择 -->
    <van-popup v-model:show="showIntlPicker" position="bottom">
      <van-picker
        :columns="intlColumns"
        @confirm="onIntlConfirm"
        @cancel="showIntlPicker = false"
      />
    </van-popup>

    <!-- 币种选择 -->
    <van-popup v-model:show="showCurrencyPicker" position="bottom">
      <van-picker
        :columns="currencyColumns"
        @confirm="onCurrencyConfirm"
        @cancel="showCurrencyPicker = false"
      />
    </van-popup>

    <!-- 费用归属选择 -->
    <van-popup v-model:show="showPayerPicker" position="bottom">
      <van-picker
        :columns="payerColumns"
        @confirm="onPayerConfirm"
        @cancel="showPayerPicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.m-logistics-form {
  min-height: 100vh;
  background: #f7f8fa;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.action-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
}
</style>
