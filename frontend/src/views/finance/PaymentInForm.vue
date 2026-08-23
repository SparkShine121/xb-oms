<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createPaymentIn } from '../../api/finance'
import { listOrders } from '../../api/orders'

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

async function loadOrders() {
  if (orders.value.length) return
  const resp: any = await listOrders({ page: 1, page_size: 200 })
  orders.value = resp.data.results ?? []
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
})

onMounted(loadOrders)
</script>

<template>
  <el-dialog v-model="visible" title="登记回款" width="480px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="订单" required>
        <el-select v-model="form.order" placeholder="选择订单" filterable style="width: 100%">
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
