<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '../../api/auth'
import PageHeader from '../../components/PageHeader.vue'
import DataTable from '../../components/DataTable.vue'
import AppPagination from '../../components/AppPagination.vue'
import { PhUsersThree } from '@phosphor-icons/vue'

interface UserItem {
  id: number
  username: string
  email: string
  groups: string[]
  is_active?: boolean
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
const form = reactive({ username: '', email: '', password: '', group: '' as string })

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
  form.group = ''
  dialogVisible.value = true
}

function openEdit(u: UserItem) {
  editingId.value = u.id
  form.username = u.username
  form.email = u.email
  form.password = ''
  form.group = u.groups[0] ?? ''
  dialogVisible.value = true
}

async function save() {
  if (!form.username.trim()) return ElMessage.warning('请输入用户名')
  if (!editingId.value && !form.password) return ElMessage.warning('请输入初始密码')
  saving.value = true
  try {
    const payload: any = { username: form.username.trim(), email: form.email, groups: form.group ? [form.group] : [] }
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

// BUG-SIM-021 Q1:b：名下有数据时必须选承接人（后端 400 提示数据量）
async function remove(u: UserItem) {
  let transferTo: number | undefined
  try {
    await ElMessageBox.confirm(`确定删除用户「${u.username}」？`, '删除确认', { type: 'warning' })
    await deleteUser(u.id)
  } catch (e: any) {
    if (e?.response?.status !== 400) throw e
    ElMessageBox.close?.()
    // 后端 400：需要承接人——弹承接人选择框
    const others = users.value.filter(x => x.id !== u.id)
    const { value } = await ElMessageBox.prompt(
      String(e.response.data?.message || '该用户名下有业务数据，请选择承接人'),
      '选择承接人', {
        inputType: 'number',
        inputPlaceholder: '输入承接人用户 ID',
        inputValidator: (v: string) => {
          const id = Number(v)
          return others.some(x => x.id === id) ? true : `请输入其他用户的 ID（如 ${others[0]?.id ?? '无'}）`
        },
      })
    transferTo = Number(value)
    await deleteUser(u.id, transferTo)
  }
  ElMessage.success('已删除')
  load()
}

// BUG-SIM-028 Q2:a：停用/启用开关（停用即时生效：access 下一请求 401 + refresh 拉黑）
async function toggleActive(u: UserItem) {
  const next = !u.is_active
  await ElMessageBox.confirm(
    `确定${next ? '启用' : '停用'}用户「${u.username}」？${next ? '' : '停用后该账号立即无法访问系统'}`,
    next ? '启用确认' : '停用确认', { type: next ? 'info' : 'warning' })
  await updateUser(u.id, { is_active: next })
  ElMessage.success(next ? '已启用' : '已停用')
  load()
}

function roleLabel(name: string) {
  return ROLE_OPTIONS.find(r => r.name === name)?.label ?? name
}

onMounted(load)
</script>

<template>
  <div class="user-manage">
    <PageHeader title="用户管理">
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </PageHeader>

    <DataTable
      :loading="loading"
      :data="users"
      border
      stripe
      empty-title="还没有用户"
      :empty-icon="PhUsersThree"
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column label="角色" min-width="200">
        <template #default="{ row }">
          <el-tag v-for="g in row.groups" :key="g" class="role-tag" size="small">{{ roleLabel(g) }}</el-tag>
          <span v-if="!row.groups.length" class="no-role">无角色</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active === false ? 'danger' : 'success'" size="small">
            {{ row.is_active === false ? '已停用' : '正常' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.is_active === false" link type="success" size="small" @click="toggleActive(row)">启用</el-button>
          <el-button v-else link type="warning" size="small" @click="toggleActive(row)">停用</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>

      <template #footer>
        <AppPagination v-model:page="page" v-model:page-size="pageSize" :total="total" @change="load" />
      </template>
    </DataTable>

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
          <el-radio-group v-model="form.group">
            <el-radio v-for="r in ROLE_OPTIONS" :key="r.name" :value="r.name">{{ r.label }}</el-radio>
          </el-radio-group>
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
.role-tag {
  margin-right: 6px;
}
.no-role {
  color: var(--dim);
  font-size: 13px;
}
</style>
