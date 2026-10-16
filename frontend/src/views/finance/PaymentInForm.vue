<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createPaymentIn } from '../../api/finance'
import { listOrders, getOrder } from '../../api/orders'

const props = defineProps<{ modelValue: boolean; presetOrderId?: number | null }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void; (e: 'saved'): void }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

const form = reactive({
  order: null as number | null,
  amount_usd: 0 as number,
  payment_date: '',
  installment: 1,
  note: '',
})

const orders = ref<any[]>([])
const saving = ref(false)
const searching = ref(false)

// BUG-SIM-031 Q3:a：远程搜索下拉——首屏 20 条，输入实时 ?search=（千单库可直达）
async function loadOrders(query?: string) {
  searching.value = true
  try {
    const resp: any = await listOrders({ page: 1, page_size: 20, search: query || undefined })
    orders.value = resp.data.results ?? []
  } finally {
    searching.value = false
  }
}

async function searchOrders(query: string) {
  await loadOrders(query.trim() || undefined)
}

// 预置订单（从订单详情跳入）：按 ID 精确拉取塞进选项，保证回显
async function ensurePresetOrder() {
  const pid = props.presetOrderId
  if (!pid) return
  if (orders.value.some(o => o.id === pid)) return
  try {
    const resp: any = await getOrder(pid)
    orders.value.unshift(resp.data)
  } catch { /* 订单不可见时静默（回显为空由用户重选） */ }
}

function reset() {
  form.order = props.presetOrderId ?? null
  form.amount_usd = 0
  form.payment_date = ''
  form.installment = 1
  form.note = ''
}

async function save() {
  if (!form.order) return ElMessage.warning('请选择订单')
  if (!form.amount_usd || form.amount_usd <= 0) return ElMessage.warning('请填写到账金额')
  if (!form.payment_date) return ElMessage.warning('请选择到账日期')
  saving.value = true
  try {
    await createPaymentIn({ ...form })
    ElMessage.success('回款登记成功')
    visible.value = false
    emit('saved')
  } finally {
    saving.value = false
  }
}

defineExpose({ loadOrders })

// 每次打开弹窗：重置表单（含预选订单）并确保订单下拉已加载
watch(() => props.modelValue, async v => {
  if (!v) return
  reset()
  await loadOrders()
  await ensurePresetOrder()
})

onMounted(loadOrders)
</script>

<template>
  <el-dialog v-model="visible" title="登记回款" width="480px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="订单" required>
        <el-select v-model="form.order" placeholder="输入订单号搜索" filterable remote :remote-method="searchOrders" :loading="searching" style="width: 100%">
          <el-option v-for="o in orders" :key="o.id" :label="o.order_no" :value="o.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="到账金额(USD)" required>
        <el-input-number v-model="form.amount_usd" :min="0.01" :precision="2" :step="100" style="width: 100%" />
      </el-form-item>
      <el-form-item label="到账日期" required>
        <el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
      </el-form-item>
      <el-form-item label="期数">
        <el-input-number v-model="form.installment" :min="1" :step="1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.note" type="textarea" :rows="3" placeholder="备注（可空）" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>
