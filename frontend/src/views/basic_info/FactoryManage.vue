<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listFactories, createFactory, updateFactory, deleteFactory,
  importFactories, downloadFactoryTemplate,
} from '../../api/basicInfo'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const resp: any = await listFactories({ page: page.value, page_size: pageSize.value, search: search.value || undefined })
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
const form = reactive({ name: '', alias: '', contact: '', phone: '', settle_currency: 'CNY', remark: '' })

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', alias: '', contact: '', phone: '', settle_currency: 'CNY', remark: '' })
  drawerVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, alias: row.alias, contact: row.contact, phone: row.phone, settle_currency: row.settle_currency, remark: row.remark })
  drawerVisible.value = true
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('工厂名称必填')
  saving.value = true
  try {
    if (editingId.value) await updateFactory(editingId.value, { ...form })
    else await createFactory({ ...form })
    ElMessage.success('保存成功')
    drawerVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除工厂「${row.name}」？`, '删除确认', { type: 'warning' })
  await deleteFactory(row.id)
  ElMessage.success('已删除')
  load()
}

// ---- 批量导入 / 模板下载 ----
const importFile = ref<File | null>(null)
const importResult = ref<any>(null)
const resultVisible = ref(false)

function onFileChange(uploadFile: any) {
  importFile.value = uploadFile.raw ?? null
}

async function doImport() {
  if (!importFile.value) return ElMessage.warning('请先选择 Excel 文件')
  const resp: any = await importFactories(importFile.value)
  importResult.value = resp.data
  resultVisible.value = true
  importFile.value = null
  load()
}

async function downloadTemplate() {
  const blob: Blob = (await downloadFactoryTemplate()) as any
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'factory_import_template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<template>
  <div class="factory-manage">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索名称 / 别名 / 联系人" clearable style="width: 240px" @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
        <el-button type="primary" @click="page = 1; load()">查询</el-button>
        <div class="toolbar-right">
          <el-upload :auto-upload="false" :limit="1" accept=".xlsx,.xls" :on-change="onFileChange" :on-remove="() => (importFile = null)" :on-exceed="() => ElMessage.warning('仅支持导入 1 个文件')">
            <el-button>选择 Excel</el-button>
          </el-upload>
          <el-button type="primary" plain :disabled="!importFile" @click="doImport">批量导入</el-button>
          <el-button @click="downloadTemplate">下载模板</el-button>
          <el-button type="primary" @click="openCreate">新增工厂</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="name" label="工厂名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="alias" label="别名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="contact" label="联系人" width="110" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="settle_currency" label="结算币种" width="100" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
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

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑工厂' : '新增工厂'" size="480px">
      <el-form label-width="110px">
        <el-form-item label="工厂名称" required>
          <el-input v-model="form.name" placeholder="唯一名称" />
        </el-form-item>
        <el-form-item label="别名">
          <el-input v-model="form.alias" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="结算币种">
          <el-select v-model="form.settle_currency" style="width: 100%">
            <el-option v-for="c in ['CNY', 'USD', 'EUR', 'HKD']" :key="c" :label="c" :value="c" />
          </el-select>
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

    <el-dialog v-model="resultVisible" title="批量导入结果" width="480px">
      <template v-if="importResult">
        <p>成功 {{ importResult.success_count }} 条，失败 {{ importResult.fail_count }} 条</p>
        <el-table v-if="importResult.failures?.length" :data="importResult.failures" size="small" max-height="260">
          <el-table-column prop="row" label="行号" width="70" />
          <el-table-column prop="reason" label="失败原因" />
        </el-table>
      </template>
      <template #footer>
        <el-button type="primary" @click="resultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
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
