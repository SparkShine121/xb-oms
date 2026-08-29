<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryTree, createCategory, updateCategory, deleteCategory, bulkDeleteCategories } from '../../api/basicInfo'

interface CategoryNode {
  id: number
  name: string
  parent: number | null
  sort_order: number
  children?: CategoryNode[]
}

const treeData = ref<CategoryNode[]>([])
const treeRef = ref()
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', parent: null as number | null, sort_order: 0 })

const flatNodes = computed(() => {
  const out: { id: number; name: string }[] = []
  const walk = (nodes: CategoryNode[], depth = 0) => {
    for (const n of nodes) {
      out.push({ id: n.id, name: '　'.repeat(depth) + n.name })
      if (n.children?.length) walk(n.children, depth + 1)
    }
  }
  walk(treeData.value)
  return out
})

async function loadTree() {
  const resp: any = await categoryTree()
  treeData.value = resp.data
}

function openCreate(parent: number | null) {
  editingId.value = null
  form.name = ''
  form.parent = parent
  form.sort_order = 0
  dialogVisible.value = true
}

function openEdit(node: CategoryNode) {
  editingId.value = node.id
  form.name = node.name
  form.parent = node.parent
  form.sort_order = node.sort_order
  dialogVisible.value = true
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请输入类目名称')
  saving.value = true
  try {
    const payload = { name: form.name.trim(), parent: form.parent, sort_order: form.sort_order }
    if (editingId.value) await updateCategory(editingId.value, payload)
    else await createCategory(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadTree()
  } finally {
    saving.value = false
  }
}

async function remove(node: CategoryNode) {
  await ElMessageBox.confirm(`确定删除类目「${node.name}」？其下所有子类目将一并删除。`, '删除确认', { type: 'warning' })
  await deleteCategory(node.id)
  ElMessage.success('已删除')
  loadTree()
}

onMounted(loadTree)

async function handleBatchDelete() {
  const ids = (treeRef.value?.getCheckedKeys() as number[]) ?? []
  if (!ids.length) return ElMessage.warning('请先勾选要删除的类目')
  await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 个类目？其下所有子类目将一并删除。`, '批量删除', { type: 'warning' })
  await bulkDeleteCategories(ids)
  ElMessage.success('已删除')
  loadTree()
}
</script>

<template>
  <div class="category-manage">
    <div class="toolbar">
      <el-button type="primary" @click="openCreate(null)">新增根类目</el-button>
      <el-button type="danger" plain @click="handleBatchDelete">批量删除</el-button>
    </div>
    <el-card shadow="never">
      <el-tree ref="treeRef" :data="treeData" node-key="id" :props="{ children: 'children', label: 'name' }" default-expand-all show-checkbox>
        <template #default="{ data }">
          <div class="tree-node">
            <span class="tree-label">{{ data.name }}</span>
            <span class="tree-actions">
              <el-button link type="primary" size="small" @click="openCreate(data.id)">新增子类</el-button>
              <el-button link type="primary" size="small" @click="openEdit(data)">编辑</el-button>
              <el-button link type="danger" size="small" @click="remove(data)">删除</el-button>
            </span>
          </div>
        </template>
      </el-tree>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑类目' : '新增类目'" width="420px">
      <el-form label-width="80px">
        <el-form-item label="类目名称" required>
          <el-input v-model="form.name" placeholder="如：名片 / 画册 / 包装" />
        </el-form-item>
        <el-form-item label="上级类目">
          <el-select v-model="form.parent" clearable placeholder="无（根类目）" style="width: 100%">
            <el-option v-for="n in flatNodes" :key="n.id" :label="n.name" :value="n.id" :disabled="n.id === editingId" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
.tree-node {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-right: 16px;
}
.tree-label {
  font-size: 14px;
}
.tree-actions {
  visibility: hidden;
}
.tree-node:hover .tree-actions {
  visibility: visible;
}
</style>
