<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listLogistics, createLogistics, updateLogistics, deleteLogistics } from '../../api/basicInfo'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const typeFilter = ref('')
const loading = ref(false)

const TYPE_OPTIONS = [
  { value: 'domestic', label: '国内' },
  { value: 'international', label: '国际' },
]
const typeLabel = (t: string) => TYPE_OPTIONS.find(o => o.value === t)?.label ?? t

async function load() {
  loading.value = true
  try {
    const resp: any = await listLogistics({ page: page.value, page_size: pageSize.value, search: search.value || undefined, type: typeFilter.value || undefined })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

// ---- 新增 / 编辑 ----
const drawerVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', type: 'domestic', contact: '', phone: '', remark: '' })

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', type: 'domestic', contact: '', phone: '', remark: '' })
  drawerVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, type: row.type, contact: row.contact, phone: row.phone, remark: row.remark })
  drawerVisible.value = true
}

async function save() {
  if (!form.name.trim() || !form.type) return ElMessage.warning('名称与类型必填')
  saving.value = true
  try {
    if (editingId.value) await updateLogistics(editingId.value, { ...form })
    else await createLogistics({ ...form })
    ElMessage.success('保存成功')
    drawerVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除物流商「${row.name}」？`, '删除确认', { type: 'warning' })
  await deleteLogistics(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div class="logistics-manage">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索名称 / 联系人" clearable style="width: 220px" @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
        <el-select v-model="typeFilter" clearable placeholder="全部类型" style="width: 140px" @change="page = 1; load()">
          <el-option v-for="o in TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="page = 1; load()">查询</el-button>
        <div class="toolbar-right">
          <el-button type="primary" @click="openCreate">新增物流商</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'international' ? 'warning' : 'primary'" size="small">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact" label="联系人" width="110" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pager"
        @current-change="load"
        @size-change="page = 1; load()"
      />
    </el-card>

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑物流商' : '新增物流商'" size="480px">
      <el-form label-width="110px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type" style="width: 100%">
            <el-option v-for="o in TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
