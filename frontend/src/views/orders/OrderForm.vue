<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createOrder, updateOrder, getOrder } from '../../api/orders'
import { listCustomers, listFactories } from '../../api/basicInfo'
import { listUsers } from '../../api/auth'
import { useUserStore } from '../../stores/user'

const props = defineProps<{ id?: string | number }>()
const router = useRouter()
const userStore = useUserStore()
const roles = computed(() => userStore.roles)
const isAdmin = computed(() => roles.value.includes('admin'))
const isEdit = computed(() => !!props.id)

const TRACKING_STATUS_OPTIONS = ['接单', '排产', '生产中', '质检', '发货', '签收', '结算', '回款', '已取消']

const form = reactive({
  order_no: '',
  ali_status: '',
  tracking_status: '',
  order_date: null as string | null,
  customer: null as number | null,
  salesman: null as number | null,
  tracker: null as number | null,
  amount_usd: 0 as number,
  freight: 0 as number,
  insurance: 0 as number,
  surcharge: 0 as number,
  service_fee_usd: 0 as number,
  transport_cost: 0 as number,
  carrier: '',
  logistics_method: '',
  tracking_no: '',
  remark: '',
})

const items = ref<any[]>([])

const customers = ref<any[]>([])
const factories = ref<any[]>([])
const salesmen = ref<any[]>([])
const allUsers = ref<any[]>([])

const saving = ref(false)
const loading = ref(false)

async function loadOptions() {
  const [custResp, facResp, userResp] = await Promise.all([
    listCustomers({ page: 1, page_size: 500 }),
    listFactories({ page: 1, page_size: 500 }),
    listUsers({ page: 1, page_size: 200 }),
  ])
  customers.value = (custResp as any).data.results ?? []
  factories.value = (facResp as any).data.results ?? []
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
      factory: it.factory ?? null,
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
    factory: null as number | null,
  })
}

function removeItem(index: number) {
  items.value.splice(index, 1)
}

function calcSubtotal(row: any) {
  row.subtotal = Number(row.qty) * Number(row.unit_price) || 0
}

async function save() {
  if (!form.order_no.trim()) return ElMessage.warning('订单号必填')
  saving.value = true
  try {
    const payload = {
      ...form,
      items: items.value.map((it: any) => ({
        seq: it.seq,
        product_no: it.product_no,
        model: it.model,
        spec: it.spec,
        qty: it.qty,
        unit_price: it.unit_price,
        subtotal: it.subtotal,
        cost_price: it.cost_price,
        factory: it.factory,
      })),
    }
    if (isEdit.value) {
      await updateOrder(Number(props.id), payload)
    } else {
      await createOrder(payload)
    }
    ElMessage.success('保存成功')
    router.push('/orders/list')
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
  <div class="order-form" v-loading="loading">
    <div class="form-header">
      <el-button @click="cancel">返回</el-button>
      <span class="form-title">{{ isEdit ? '编辑订单' : '新增订单' }}</span>
    </div>

    <el-card shadow="never">
      <template #header>订单信息</template>
      <el-form label-width="120px">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="订单号" required>
              <el-input v-model="form.order_no" :disabled="isEdit" placeholder="请输入订单号" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="阿里状态">
              <el-input v-model="form.ali_status" placeholder="阿里状态" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="跟踪状态">
              <el-select v-model="form.tracking_status" clearable placeholder="选择跟踪状态" style="width: 100%">
                <el-option v-for="s in TRACKING_STATUS_OPTIONS" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="订单日期">
              <el-date-picker
                v-model="form.order_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户">
              <el-select v-model="form.customer" clearable filterable placeholder="选择客户" style="width: 100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="业务员">
              <el-select v-model="form.salesman" clearable filterable placeholder="选择业务员" style="width: 100%">
                <el-option v-for="s in salesmen" :key="s.id" :label="s.username" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="跟单员">
              <el-select
                v-model="form.tracker"
                clearable
                filterable
                placeholder="选择跟单员"
                style="width: 100%"
                :disabled="!isAdmin"
              >
                <el-option v-for="u in allUsers" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="订单金额(USD)">
              <el-input-number v-model="form.amount_usd" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="运费">
              <el-input-number v-model="form.freight" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="物流保险费">
              <el-input-number v-model="form.insurance" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="附加费用">
              <el-input-number v-model="form.surcharge" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="交易服务费(USD)">
              <el-input-number v-model="form.service_fee_usd" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="运输成本">
              <el-input-number v-model="form.transport_cost" :precision="2" :step="0.01" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="承运商">
              <el-input v-model="form.carrier" placeholder="承运商" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="物流方式">
              <el-input v-model="form.logistics_method" placeholder="物流方式" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="物流单号">
              <el-input v-model="form.tracking_no" placeholder="物流单号" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>产品明细</span>
          <el-button type="primary" size="small" @click="addItem">增行</el-button>
        </div>
      </template>
      <el-table :data="items" border stripe size="small" :empty-text="'暂无产品明细，点击「增行」添加'">
        <el-table-column label="序号" width="80">
          <template #default="{ row }">
            <el-input-number v-model="row.seq" :controls="false" :precision="0" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="产品编号" min-width="140">
          <template #default="{ row }">
            <el-input v-model="row.product_no" placeholder="产品编号" />
          </template>
        </el-table-column>
        <el-table-column label="型号" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.model" placeholder="型号" />
          </template>
        </el-table-column>
        <el-table-column label="规格" min-width="160">
          <template #default="{ row }">
            <el-input v-model="row.spec" placeholder="规格" />
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.qty"
              :controls="false"
              :precision="0"
              style="width: 100%"
              @change="calcSubtotal(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="单价(USD)" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.unit_price"
              :controls="false"
              :precision="2"
              :step="0.01"
              style="width: 100%"
              @change="calcSubtotal(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="小计(USD)" width="120">
          <template #default="{ row }">
            <el-input-number v-model="row.subtotal" :controls="false" :precision="2" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="成本价(CNY)" width="120">
          <template #default="{ row }">
            <el-input-number v-model="row.cost_price" :controls="false" :precision="2" :step="0.01" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="工厂" min-width="140">
          <template #default="{ row }">
            <el-select v-model="row.factory" clearable filterable placeholder="选择工厂" style="width: 100%">
              <el-option v-for="f in factories" :key="f.id" :label="f.name" :value="f.id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" size="small" @click="removeItem($index)">删行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="form-footer">
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </div>
  </div>
</template>

<style scoped>
.order-form {
  max-width: 1200px;
}
.form-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.form-title {
  font-size: 16px;
  font-weight: 600;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>