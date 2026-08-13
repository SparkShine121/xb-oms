<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createOrder, updateOrder, getOrder } from '../../../api/orders'
import { listCustomers } from '../../../api/basicInfo'
import { listUsers } from '../../../api/auth'
import { useUserStore } from '../../../stores/user'

const props = defineProps<{ id?: string | number }>()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const isAdmin = computed(() => roles.value.includes('admin'))
const isEdit = computed(() => !!props.id)

const TRACKING_STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款', '已取消']
const trackingStatusColumns = TRACKING_STATUS_OPTIONS.map(s => ({ text: s, value: s }))

const form = reactive({
  order_no: '',
  ali_status: '',
  tracking_status: '',
  order_date: null as string | null,
  customer: null as number | null,
  salesman: null as number | null,
  tracker: null as number | null,
  amount_usd: 0 as number | string,
  freight: 0 as number | string,
  insurance: 0 as number | string,
  surcharge: 0 as number | string,
  service_fee_usd: 0 as number | string,
  transport_cost: 0 as number | string,
  carrier: '',
  logistics_method: '',
  tracking_no: '',
  remark: '',
})

const items = ref<any[]>([])
const customers = ref<any[]>([])
const salesmen = ref<any[]>([])
const allUsers = ref<any[]>([])
const saving = ref(false)
const loading = ref(false)

// Picker 弹窗显示状态
const showTrackingStatusPicker = ref(false)
const showDatePicker = ref(false)
const showCustomerPicker = ref(false)
const showSalesmanPicker = ref(false)
const showTrackerPicker = ref(false)
const datePickerValue = ref<string[]>([])

// Picker 列数据
const customerColumns = computed(() => customers.value.map((c: any) => ({ text: c.name, value: c.id })))
const salesmanColumns = computed(() => salesmen.value.map((s: any) => ({ text: s.username, value: s.id })))
const trackerColumns = computed(() => allUsers.value.map((u: any) => ({ text: u.username, value: u.id })))

// Picker 字段显示文本
const customerText = computed(() => customers.value.find((c: any) => c.id === form.customer)?.name || '')
const salesmanText = computed(() => salesmen.value.find((s: any) => s.id === form.salesman)?.username || '')
const trackerText = computed(() => allUsers.value.find((u: any) => u.id === form.tracker)?.username || '')

async function loadOptions() {
  const [custResp, userResp] = await Promise.all([
    listCustomers({ page: 1, page_size: 500 }),
    listUsers({ page: 1, page_size: 200 }),
  ])
  customers.value = (custResp as any).data.results ?? []
  const all = (userResp as any).data.results ?? []
  allUsers.value = all
  salesmen.value = all.filter((u: any) => u.groups?.includes('salesman'))
}

async function loadOrder() {
  if (!props.id) return
  loading.value = true
  try {
    const resp: any = await getOrder(Number(props.id))
    const d = resp.data
    Object.assign(form, {
      order_no: d.order_no ?? '',
      ali_status: d.ali_status ?? '',
      tracking_status: d.tracking_status ?? '',
      order_date: d.order_date ?? null,
      customer: d.customer ?? null,
      salesman: d.salesman ?? null,
      tracker: d.tracker ?? null,
      amount_usd: Number(d.amount_usd) || 0,
      freight: Number(d.freight) || 0,
      insurance: Number(d.insurance) || 0,
      surcharge: Number(d.surcharge) || 0,
      service_fee_usd: Number(d.service_fee_usd) || 0,
      transport_cost: Number(d.transport_cost) || 0,
      carrier: d.carrier ?? '',
      logistics_method: d.logistics_method ?? '',
      tracking_no: d.tracking_no ?? '',
      remark: d.remark ?? '',
    })
    items.value = (d.items ?? []).map((it: any) => ({
      seq: it.seq ?? 0,
      product_no: it.product_no ?? '',
      model: it.model ?? '',
      spec: it.spec ?? '',
      qty: Number(it.qty) || 0,
      unit_price: Number(it.unit_price) || 0,
      subtotal: Number(it.subtotal) || 0,
      cost_price: Number(it.cost_price) || 0,
    }))
  } finally {
    loading.value = false
  }
}

function addItem() {
  const nextSeq = items.value.length ? Math.max(...items.value.map((i: any) => Number(i.seq) || 0)) + 1 : 1
  items.value.push({
    seq: nextSeq,
    product_no: '',
    model: '',
    spec: '',
    qty: 0,
    unit_price: 0,
    subtotal: 0,
    cost_price: 0,
  })
}

function removeItem(index: number) {
  items.value.splice(index, 1)
}

function calcSubtotal(row: any) {
  row.subtotal = (Number(row.qty) * Number(row.unit_price)) || 0
}

function openDatePicker() {
  if (form.order_date) {
    datePickerValue.value = form.order_date.split('-')
  } else {
    const today = new Date().toISOString().slice(0, 10)
    datePickerValue.value = today.split('-')
  }
  showDatePicker.value = true
}

function onDateConfirm({ selectedValues }: { selectedValues: string[] }) {
  form.order_date = selectedValues.join('-')
  showDatePicker.value = false
}

function onTrackingStatusConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.tracking_status = v != null ? String(v) : ''
  showTrackingStatusPicker.value = false
}

function onCustomerConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.customer = v != null ? Number(v) : null
  showCustomerPicker.value = false
}

function onSalesmanConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.salesman = v != null ? Number(v) : null
  showSalesmanPicker.value = false
}

function onTrackerConfirm({ selectedValues }: { selectedValues: (string | number)[] }) {
  const v = selectedValues[0]
  form.tracker = v != null ? Number(v) : null
  showTrackerPicker.value = false
}

async function onSubmit() {
  saving.value = true
  try {
    const payload = {
      ...form,
      amount_usd: Number(form.amount_usd) || 0,
      freight: Number(form.freight) || 0,
      insurance: Number(form.insurance) || 0,
      surcharge: Number(form.surcharge) || 0,
      service_fee_usd: Number(form.service_fee_usd) || 0,
      transport_cost: Number(form.transport_cost) || 0,
      items: items.value.map((it: any) => ({
        seq: it.seq,
        product_no: it.product_no,
        model: it.model,
        spec: it.spec,
        qty: Number(it.qty) || 0,
        unit_price: Number(it.unit_price) || 0,
        subtotal: Number(it.subtotal) || 0,
        cost_price: Number(it.cost_price) || 0,
      })),
    }
    if (isEdit.value) {
      await updateOrder(Number(props.id), payload)
    } else {
      await createOrder(payload)
    }
    router.push('/m/orders')
  } finally {
    saving.value = false
  }
}

function cancel() {
  router.back()
}

onMounted(async () => {
  await loadOptions()
  if (isEdit.value) await loadOrder()
})
</script>

<template>
  <div class="m-order-form">
    <van-nav-bar :title="isEdit ? '编辑订单' : '新增订单'" left-arrow @click-left="cancel" />

    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" />
    </div>

    <van-form v-else @submit="onSubmit">
      <van-cell-group inset title="订单信息">
        <van-field
          v-model="form.order_no"
          name="order_no"
          label="订单号"
          required
          :rules="[{ required: true, message: '请输入订单号' }]"
          :disabled="isEdit"
          placeholder="请输入订单号"
        />
        <van-field
          v-model="form.ali_status"
          label="阿里状态"
          placeholder="阿里状态"
        />
        <van-field
          :model-value="form.tracking_status"
          is-link
          readonly
          label="跟踪状态"
          placeholder="选择跟踪状态"
          @click="showTrackingStatusPicker = true"
        />
        <van-field
          :model-value="form.order_date || ''"
          is-link
          readonly
          label="订单日期"
          placeholder="选择日期"
          @click="openDatePicker"
        />
        <van-field
          :model-value="customerText"
          is-link
          readonly
          label="客户"
          placeholder="选择客户"
          @click="showCustomerPicker = true"
        />
        <van-field
          :model-value="salesmanText"
          is-link
          readonly
          label="业务员"
          placeholder="选择业务员"
          @click="showSalesmanPicker = true"
        />
        <van-field
          v-if="isAdmin"
          :model-value="trackerText"
          is-link
          readonly
          label="跟单员"
          placeholder="选择跟单员"
          @click="showTrackerPicker = true"
        />
        <van-field
          v-model="form.amount_usd"
          type="number"
          label="订单金额(USD)"
          placeholder="0.00"
        />
        <van-field
          v-model="form.freight"
          type="number"
          label="运费"
          placeholder="0.00"
        />
        <van-field
          v-model="form.insurance"
          type="number"
          label="物流保险费"
          placeholder="0.00"
        />
        <van-field
          v-model="form.surcharge"
          type="number"
          label="附加费用"
          placeholder="0.00"
        />
        <van-field
          v-model="form.service_fee_usd"
          type="number"
          label="交易服务费(USD)"
          placeholder="0.00"
        />
        <van-field
          v-model="form.transport_cost"
          type="number"
          label="运输成本"
          placeholder="0.00"
        />
        <van-field
          v-model="form.carrier"
          label="承运商"
          placeholder="承运商"
        />
        <van-field
          v-model="form.logistics_method"
          label="物流方式"
          placeholder="物流方式"
        />
        <van-field
          v-model="form.tracking_no"
          label="物流单号"
          placeholder="物流单号"
        />
        <van-field
          v-model="form.remark"
          type="textarea"
          label="备注"
          placeholder="备注"
          rows="2"
          autosize
        />
      </van-cell-group>

      <van-cell-group inset title="产品明细" class="items-group">
        <van-empty v-if="!items.length" description="暂无产品明细，点击「添加产品」" />
        <div v-for="(item, idx) in items" :key="idx" class="product-row">
          <van-cell :title="`#${item.seq}`" center>
            <template #value>
              <van-button size="mini" type="danger" plain native-type="button" @click="removeItem(idx)">
                删除
              </van-button>
            </template>
          </van-cell>
          <van-field v-model="item.product_no" label="产品编号" placeholder="产品编号" />
          <van-field v-model="item.model" label="型号" placeholder="型号" />
          <van-field v-model="item.spec" label="规格" placeholder="规格" />
          <van-field
            :model-value="item.qty"
            @update:model-value="(v: string) => { item.qty = v; calcSubtotal(item) }"
            type="digit"
            label="数量"
            placeholder="数量"
          />
          <van-field
            :model-value="item.unit_price"
            @update:model-value="(v: string) => { item.unit_price = v; calcSubtotal(item) }"
            type="number"
            label="单价(USD)"
            placeholder="0.00"
          />
          <van-field
            v-model="item.subtotal"
            type="number"
            label="小计(USD)"
            readonly
          />
          <van-field
            v-model="item.cost_price"
            type="number"
            label="成本价(CNY)"
            placeholder="0.00"
          />
        </div>
        <div class="add-item-wrap">
          <van-button block plain type="primary" native-type="button" @click="addItem">
            添加产品
          </van-button>
        </div>
      </van-cell-group>

      <div class="action-bar">
        <van-button block @click="cancel" native-type="button">取消</van-button>
        <van-button block type="primary" native-type="submit" :loading="saving">保存</van-button>
      </div>
    </van-form>

    <!-- 跟踪状态选择 -->
    <van-popup v-model:show="showTrackingStatusPicker" position="bottom">
      <van-picker
        :columns="trackingStatusColumns"
        @confirm="onTrackingStatusConfirm"
        @cancel="showTrackingStatusPicker = false"
      />
    </van-popup>

    <!-- 订单日期选择 -->
    <van-popup v-model:show="showDatePicker" position="bottom">
      <van-date-picker
        v-model="datePickerValue"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 客户选择 -->
    <van-popup v-model:show="showCustomerPicker" position="bottom">
      <van-picker
        :columns="customerColumns"
        @confirm="onCustomerConfirm"
        @cancel="showCustomerPicker = false"
      />
    </van-popup>

    <!-- 业务员选择 -->
    <van-popup v-model:show="showSalesmanPicker" position="bottom">
      <van-picker
        :columns="salesmanColumns"
        @confirm="onSalesmanConfirm"
        @cancel="showSalesmanPicker = false"
      />
    </van-popup>

    <!-- 跟单员选择（仅 admin） -->
    <van-popup v-model:show="showTrackerPicker" position="bottom">
      <van-picker
        :columns="trackerColumns"
        @confirm="onTrackerConfirm"
        @cancel="showTrackerPicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.m-order-form {
  min-height: 100vh;
  background: #f7f8fa;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.items-group {
  margin-top: 12px;
}
.product-row + .product-row {
  margin-top: 8px;
  border-top: 8px solid #f7f8fa;
}
.add-item-wrap {
  padding: 12px 16px;
}
.action-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
}
</style>