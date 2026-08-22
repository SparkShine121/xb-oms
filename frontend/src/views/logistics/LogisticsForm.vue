<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getShipment, createShipment, updateShipment } from '../../api/logistics'
import { listOrders } from '../../api/orders'
import { listLogistics } from '../../api/basicInfo'

const props = defineProps<{ id?: string | number }>()
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!props.id)

const form = reactive({
  order: null as number | null,
  domestic_carrier: null as number | null,
  intl_method: null as number | null,
  tracking_no: '',
  cost: 0 as number,
  cost_currency: 'CNY',
  payer: 'company',
  note: '',
})

const orders = ref<any[]>([])
const domesticCarriers = ref<any[]>([])
const intlMethods = ref<any[]>([])

const saving = ref(false)
const loading = ref(false)

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

async function save() {
  if (!form.order) return ElMessage.warning('请选择订单')
  saving.value = true
  try {
    if (isEdit.value) await updateShipment(Number(props.id), { ...form })
    else await createShipment({ ...form })
    ElMessage.success('保存成功')
    router.push('/logistics')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  // 从 OrderDetail「登记发货」跳入时预选订单
  const preOrderId = Number(route.query.order_id)
  if (!isEdit.value && preOrderId) form.order = preOrderId
  await loadShipment()
})
</script>

<template>
  <div class="logistics-form" v-loading="loading">
    <el-card shadow="never">
      <template #header>{{ isEdit ? '编辑发货单' : '登记发货' }}</template>

      <el-form :model="form" label-width="110px" style="max-width: 640px">
        <el-form-item label="订单" required>
          <el-select v-model="form.order" placeholder="选择订单" filterable style="width: 100%">
            <el-option v-for="o in orders" :key="o.id" :label="o.order_no" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="国内承运商">
          <el-select v-model="form.domestic_carrier" placeholder="选择国内承运商" clearable filterable style="width: 100%">
            <el-option v-for="p in domesticCarriers" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="国际物流">
          <el-select v-model="form.intl_method" placeholder="选择国际物流方式" clearable filterable style="width: 100%">
            <el-option v-for="p in intlMethods" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号">
          <el-input v-model="form.tracking_no" placeholder="物流单号" />
        </el-form-item>
        <el-form-item label="费用">
          <div class="inline-fields">
            <el-input-number v-model="form.cost" :min="0" :precision="2" :step="1" style="width: 180px" />
            <el-select v-model="form.cost_currency" style="width: 100px">
              <el-option label="人民币" value="CNY" />
              <el-option label="美元" value="USD" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="费用归属">
          <el-select v-model="form.payer" style="width: 180px">
            <el-option label="客户" value="customer" />
            <el-option label="公司" value="company" />
            <el-option label="工厂" value="factory" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" placeholder="备注" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="router.push('/logistics')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.inline-fields {
  display: flex;
  gap: 8px;
}
</style>
