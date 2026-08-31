<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  categoryTree, listProducts, createProduct, updateProduct, deleteProduct, bulkDeleteProducts,
  importProducts, downloadProductTemplate,
} from '../../api/basicInfo'
import { useBulkDelete } from '../../composables/useBulkDelete'
import { useUserStore } from '../../stores/user'

interface CategoryNode { id: number; name: string; children?: CategoryNode[] }

const { selection, handleSelectionChange, handleBatchDelete } = useBulkDelete(bulkDeleteProducts, load)

// 基础信息写操作（新增/编辑/删除/导入）仅 admin；其他角色只读
const isAdmin = computed(() => useUserStore().roles.includes('admin'))

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const categoryFilter = ref<number | null>(null)
const loading = ref(false)

const categories = ref<CategoryNode[]>([])
const catNames = computed(() => {
  const m = new Map<number, string>()
  const walk = (nodes: CategoryNode[]) => {
    for (const n of nodes) {
      m.set(n.id, n.name)
      if (n.children?.length) walk(n.children)
    }
  }
  walk(categories.value)
  return m
})
const flatCategories = computed(() => {
  const out: { id: number; name: string }[] = []
  const walk = (nodes: CategoryNode[], depth = 0) => {
    for (const n of nodes) {
      out.push({ id: n.id, name: '　'.repeat(depth) + n.name })
      if (n.children?.length) walk(n.children, depth + 1)
    }
  }
  walk(categories.value)
  return out
})
const catName = (id: number | null) => (id && catNames.value.has(id) ? catNames.value.get(id) : '—')

async function load() {
  loading.value = true
  try {
    const resp: any = await listProducts({ page: page.value, page_size: pageSize.value, search: search.value || undefined, category: categoryFilter.value ?? undefined })
    rows.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const resp: any = await categoryTree()
  categories.value = resp.data
}

// ---- 新增 / 编辑 ----
const drawerVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  product_no: '', model: '', name: '', category: null as number | null,
  spec: '', default_price: 0, default_cost_price: 0, remark: '',
})

function openCreate() {
  editingId.value = null
  Object.assign(form, { product_no: '', model: '', name: '', category: null, spec: '', default_price: 0, default_cost_price: 0, remark: '' })
  drawerVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  Object.assign(form, {
    product_no: row.product_no, model: row.model, name: row.name, category: row.category,
    spec: row.spec, default_price: Number(row.default_price), default_cost_price: Number(row.default_cost_price),
    remark: row.remark,
  })
  drawerVisible.value = true
}

async function save() {
  if (!form.product_no.trim() || !form.name.trim()) return ElMessage.warning('产品编号与名称必填')
  saving.value = true
  try {
    if (editingId.value) await updateProduct(editingId.value, { ...form })
    else await createProduct({ ...form })
    ElMessage.success('保存成功')
    drawerVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除产品「${row.name}」？`, '删除确认', { type: 'warning' })
  await deleteProduct(row.id)
  ElMessage.success('已删除')
  load()
}

// ---- 批量导入 / 模板下载 ----
const importFile = ref<File | null>(null)
const importResult = ref<any>(null)
const resultVisible = ref(false)
const uploadRef = ref()

function onFileChange(uploadFile: any) {
  importFile.value = uploadFile.raw ?? null
}

async function doImport() {
  if (!importFile.value) return ElMessage.warning('请先选择 Excel 文件')
  const resp: any = await importProducts(importFile.value)
  importResult.value = resp.data
  resultVisible.value = true
  importFile.value = null
  uploadRef.value?.clearFiles()
  load()
}

async function downloadTemplate() {
  const blob: Blob = (await downloadProductTemplate()) as any
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'product_import_template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => { loadCategories(); load() })
</script>

<template>
  <div class="product-manage">
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索编号 / 型号 / 名称" clearable style="width: 240px" @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
        <el-select v-model="categoryFilter" clearable placeholder="全部类目" style="width: 180px" @change="page = 1; load()">
          <el-option v-for="c in flatCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="page = 1; load()">查询</el-button>
        <div class="toolbar-right">
          <template v-if="isAdmin">
            <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :on-change="onFileChange" :on-remove="() => (importFile = null)" :on-exceed="() => ElMessage.warning('仅支持导入 1 个文件')">
              <el-button>选择 Excel</el-button>
            </el-upload>
            <el-button type="primary" plain :disabled="!importFile" @click="doImport">批量导入</el-button>
          </template>
          <el-button @click="downloadTemplate">下载模板</el-button>
          <el-button v-if="isAdmin" type="danger" plain :disabled="!selection.length" @click="handleBatchDelete">批量删除</el-button>
          <el-button v-if="isAdmin" type="primary" @click="openCreate">新增产品</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="product_no" label="产品编号" width="120" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="类目" width="130">
          <template #default="{ row }">{{ catName(row.category) }}</template>
        </el-table-column>
        <el-table-column prop="spec" label="规格" min-width="140" show-overflow-tooltip />
        <el-table-column prop="default_price" label="默认售价(USD)" width="110" />
        <el-table-column prop="default_cost_price" label="成本价(CNY)" width="110" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button v-if="isAdmin" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="isAdmin" link type="danger" size="small" @click="remove(row)">删除</el-button>
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

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑产品' : '新增产品'" size="480px">
      <el-form label-width="110px">
        <el-form-item label="产品编号" required>
          <el-input v-model="form.product_no" placeholder="唯一编号" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类目">
          <el-select v-model="form.category" clearable placeholder="选择类目" style="width: 100%">
            <el-option v-for="c in flatCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.spec" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="默认售价(USD)">
          <el-input-number v-model="form.default_price" :min="0" :precision="2" :step="0.01" style="width: 100%" />
        </el-form-item>
        <el-form-item label="成本价(CNY)">
          <el-input-number v-model="form.default_cost_price" :min="0" :precision="2" :step="0.01" style="width: 100%" />
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
.toolbar .el-upload,
.toolbar-right .el-upload {
  display: inline-flex;
  align-items: center;
  height: 32px;
  margin: 0;
}
.toolbar .el-upload .el-button,
.toolbar-right .el-upload .el-button {
  margin: 0;
}
.toolbar-right > div {
  display: flex;
  align-items: center;
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
