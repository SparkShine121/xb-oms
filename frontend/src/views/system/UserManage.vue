<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '../../api/auth'

interface UserItem {
  id: number
  username: string
  email: string
  groups: string[]
}

const ROLE_OPTIONS = [
  { name: 'admin', label: '管理员' },
  { name: 'salesman', label: '业务员' },
  { name: 'tracker', label: '跟单员' },
  { name: 'finance', label: '财务' },
]

const users = ref<UserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ username: '', email: '', password: '', groups: [] as string[] })

async function load() {
  loading.value = true
  try {
    const resp: any = await listUsers({ page: page.value, page_size: pageSize.value })
    users.value = resp.data.results
    total.value = resp.data.count
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.username = ''
  form.email = ''
  form.password = ''
  form.groups = []
  dialogVisible.value = true
}

function openEdit(u: UserItem) {
  editingId.value = u.id
  form.username = u.username
  form.email = u.email
  form.password = ''
  form.groups = [...u.groups]
  dialogVisible.value = true
}

async function save() {
  if (!form.username.trim()) return ElMessage.warning('请输入用户名')
  if (!editingId.value && !form.password) return ElMessage.warning('请输入初始密码')
  saving.value = true
  try {
    const payload: any = { username: form.username.trim(), email: form.email, groups: form.groups }
    if (editingId.value) {
      if (form.password) payload.password = form.password
      await updateUser(editingId.value, payload)
    } else {
      payload.password = form.password
      await createUser(payload)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(u: UserItem) {
  await ElMessageBox.confirm(`确定删除用户「${u.username}」？`, '删除确认', { type: 'warning' })
  await deleteUser(u.id)
  ElMessage.success('已删除')
  load()
}

function roleLabel(name: string) {
  return ROLE_OPTIONS.find(r => r.name === name)?.label ?? name
}

function onPageChange(p: number) {
  page.value = p
  load()
}

onMounted(load)
</script>

<template>
  <div class="user-manage">
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>
    <el-card shadow="never">
      <el-table :data="users" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="g in row.groups" :key="g" class="role-tag" size="small">{{ roleLabel(g) }}</el-tag>
            <span v-if="!row.groups.length" class="no-role">无角色</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pager"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPageChange"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="440px">
      <el-form label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="选填" />
        </el-form-item>
        <el-form-item :label="editingId ? '重置密码' : '初始密码'" :required="!editingId">
          <el-input v-model="form.password" type="password" show-password :placeholder="editingId ? '留空则不修改' : '登录密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="form.groups">
            <el-checkbox v-for="r in ROLE_OPTIONS" :key="r.name" :value="r.name">{{ r.label }}</el-checkbox>
          </el-checkbox-group>
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
.role-tag {
  margin-right: 6px;
}
.no-role {
  color: #909399;
  font-size: 13px;
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
