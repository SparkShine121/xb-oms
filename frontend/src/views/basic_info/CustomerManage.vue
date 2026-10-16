<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listCustomers, createCustomer, updateCustomer, deleteCustomer, bulkDeleteCustomers } from '../../api/basicInfo'
import { useBulkDelete } from '../../composables/useBulkDelete'
import request from '../../api/request'
import { useUserStore } from '../../stores/user'
import PageHeader from '../../components/PageHeader.vue'
import SearchToolbar from '../../components/SearchToolbar.vue'
import DataTable from '../../components/DataTable.vue'
import AppPagination from '../../components/AppPagination.vue'
import { PhUsersThree } from '@phosphor-icons/vue'

const rows = ref<any[]>([])

// 基础信息写操作（新增/编辑/删除）仅 admin；其他角色只读
const isAdmin = computed(() => useUserStore().roles.includes('admin'))

const { selection, handleSelectionChange, handleBatchDelete } = useBulkDelete(bulkDeleteCustomers, load)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const salesmanFilter = ref<number | null>(null)
const loading = ref(false)

// 业务员列表：/auth/users/ 为 admin 专属接口，仅 admin 请求；非 admin 显示用 salesman_name，不受影响
const salesmen = ref<{ id: number; username: string }[]>([])
const trackers = ref<{ id: number; username: string }[]>([])
async function loadSalesmen() {
  if (!isAdmin.value) return
  try {
    const resp: any = await request.get('/auth/users/', { params: { page_size: 200 } })
    // 仅业务员(salesman 角色、非 admin)可被指派为客户业务员
    salesmen.value = (resp.data.results ?? []).filter(
      (u: any) => u.groups?.includes('salesman') && !u.groups?.includes('admin'),
    )
    // BUG-SIM-029 Q1:a：默认跟单员下拉（仅 tracker 角色）
    trackers.value = (resp.data.results ?? []).filter((u: any) => u.groups?.includes('tracker'))
  } catch {
    salesmen.value = []
  }
}
const salesmanName = (id: number | null) => (id ? salesmen.value.find(s => s.id === id)?.username ?? `#${id}` : '—')
const trackerName = (id: number | null) => (id ? trackers.value.find(t => t.id === id)?.username ?? `#${id}` : '—')

async function load() {
  loading.value = true
  try {
    const resp: any = await listCustomers({ page: page.value, page_size: pageSize.value, search: search.value || undefined, salesman: salesmanFilter.value ?? undefined })
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
const form = reactive({ name: '', contact_person: '', phone: '', email: '', salesman: null as number | null, tracker: null as number | null, remark: '' })

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', contact_person: '', phone: '', email: '', salesman: null, tracker: null, remark: '' })
  drawerVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, contact_person: row.contact_person, phone: row.phone, email: row.email, salesman: row.salesman, tracker: row.tracker, remark: row.remark })
  drawerVisible.value = true
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('客户名称必填')
  saving.value = true
  try {
    if (editingId.value) await updateCustomer(editingId.value, { ...form })
    else await createCustomer({ ...form })
    ElMessage.success('保存成功')
    drawerVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除客户「${row.name}」？`, '删除确认', { type: 'warning' })
  await deleteCustomer(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => { loadSalesmen(); load() })
</script>

<template>
  <div class="customer-manage">
    <PageHeader title="客户" :sub="`共 ${total} 条`">
      <el-button v-if="isAdmin" type="primary" @click="openCreate">新增客户</el-button>
    </PageHeader>

    <DataTable
      :loading="loading"
      :data="rows"
      border
      stripe
      empty-title="还没有客户"
      :empty-description="isAdmin ? '手动新增第一个客户' : ''"
      :empty-action-text="isAdmin ? '新增客户' : ''"
      :empty-icon="PhUsersThree"
      @empty-action="openCreate"
      @selection-change="handleSelectionChange"
    >
      <template #toolbar>
        <SearchToolbar>
          <template #filters>
            <el-input v-model="search" placeholder="搜索名称 / 联系人 / 电话" clearable style="width: 240px" @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
            <el-select v-if="isAdmin" v-model="salesmanFilter" clearable placeholder="全部业务员" style="width: 160px" @change="page = 1; load()">
              <el-option v-for="s in salesmen" :key="s.id" :label="s.username" :value="s.id" />
            </el-select>
            <el-button type="primary" @click="page = 1; load()">查询</el-button>
          </template>
          <template #actions>
            <el-button v-if="isAdmin" type="danger" plain :disabled="!selection.length" @click="handleBatchDelete">批量删除</el-button>
          </template>
        </SearchToolbar>
      </template>

      <el-table-column type="selection" width="48" />
      <el-table-column prop="name" label="客户名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="contact_person" label="联系人" width="110" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
      <el-table-column label="业务员" width="110">
        <template #default="{ row }">{{ row.salesman_name || salesmanName(row.salesman) }}</template>
      </el-table-column>
      <el-table-column label="默认跟单员" width="120">
        <template #default="{ row }">{{ row.tracker_name || trackerName(row.tracker) }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button v-if="isAdmin" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="isAdmin" link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>

      <template #footer>
        <AppPagination v-model:page="page" v-model:page-size="pageSize" :total="total" @change="load" />
      </template>
    </DataTable>

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑客户' : '新增客户'" size="480px">
      <el-form label-width="100px">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="归属业务员">
          <el-select v-model="form.salesman" clearable filterable placeholder="选择业务员" style="width: 100%">
            <el-option v-for="s in salesmen" :key="s.id" :label="s.username" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认跟单员">
          <el-select v-model="form.tracker" clearable filterable placeholder="选择跟单员（新单自动派单）" style="width: 100%">
            <el-option v-for="t in trackers" :key="t.id" :label="t.username" :value="t.id" />
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
  </div>
</template>
